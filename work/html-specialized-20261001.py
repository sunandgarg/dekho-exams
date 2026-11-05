"""Add specialized HTML lessons and a linked review quiz to the preview fixture."""

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


def add(slug, section, title, definition, situation, sample, contract, cost, mistakes, related):
    lessons.append((slug, section, title, definition, situation, sample, contract, cost, mistakes, related))


add("doctype-and-quirks-mode", "core", "HTML doctype: keep the browser in standards mode",
    "The HTML doctype selects standards mode before the browser lays out the rest of a document.",
    "A claims portal renders a printable decision and a screen version from the same template. Put the doctype first so layout rules do not depend on legacy quirks behavior. The declaration is short because HTML does not use it to select a schema or a particular browser version. The rest of the head still needs an encoding declaration, a title that identifies this decision, and a language on the root element.",
    '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Claim C-47 decision</title>
</head>
<body>
  <main><h1>Claim C-47 decision</h1><p>Review pending.</p></main>
</body>
</html>''',
    "Standards mode concerns rendering and layout. It does not prove that the document is well formed, accessible, or connected to a valid claim; those are separate checks. Inspect document.compatMode when investigating a legacy template with unexplained sizing.",
    "The doctype transfers only a few bytes. Omitting it may trigger compatibility rules whose debugging cost far exceeds the bytes saved, particularly when older stylesheets rely on box measurements.",
    ["Do not move the doctype below comments or visible content.", "Do not treat the doctype as a substitute for HTML validation.", "Do not assume a valid title or language follows from standards mode."],
    ["html/document-skeleton", "html/parser-and-void-elements", "html/metadata-title"])

add("search-element", "semantics", "HTML search element: mark a search interface by purpose",
    "The search element identifies a region containing controls for finding content.",
    "A case archive has a site search separate from the current case's review form. Wrapping the search form in search gives the region a clear purpose without changing what the server receives. The form still needs a real action and a named query control. The input label describes the thing being searched; the button states the action. If the page contains several search regions, give each an accessible name that distinguishes its scope.",
    '''<search aria-label="Case archive search">
  <form action="/cases/search" method="get">
    <label for="case-query">Find a case by reference</label>
    <input id="case-query" name="query" type="search" required>
    <button type="submit">Search cases</button>
  </form>
</search>''',
    "The server must implement the local search route and handle missing, long, or hostile query values. Search markup does not index records, rank results, or restrict which cases a user may see.",
    "The element has negligible runtime cost. Search latency comes from the endpoint and its index; measure that separately from the cost of rendering one small form.",
    ["Do not wrap every filter in a site-wide search region.", "Do not omit a label because the control has type search.", "Do not expose private cases solely because a query matches."],
    ["html/landmarks", "html/forms-get-post", "html/form-labels"])

add("address-contact-info", "semantics", "HTML address: identify contact details for the right owner",
    "The address element marks contact information for the nearest article or for the document as a whole.",
    "A claims decision includes the team responsible for its content. Place that team's contact details in the article, where their ownership is clear. A delivery destination in the claim record is ordinary data and should not be marked as the article author's address. The link below is an internal contact route so the example works without exposing a person's email address in page source.",
    '''<article>
  <h1>Claim C-47 decision</h1>
  <p>The review team requested one more document.</p>
  <address>
    Decision owner: Claims Review Team.
    <a href="/support/claims">Contact the claims team</a>.
  </address>
</article>''',
    "The local contact route needs a real handler. Address does not certify a person's identity, update a case, or create a postal address; it describes who can be contacted about this content.",
    "Semantic markup costs almost nothing to load. The maintenance cost is accuracy: review ownership and contact routes when teams or case responsibilities change.",
    ["Do not use address for every postal location shown in an article.", "Do not put an unrelated corporate footer inside a case article's address.", "Do not publish a contact route that leads nowhere."],
    ["html/sections-and-articles", "html/landmarks", "html/anchors-and-paths"])

add("ruby-annotations", "semantics", "HTML ruby: attach short pronunciation notes to text",
    "Ruby markup associates a short annotation with the text it explains, commonly for pronunciation.",
    "A bilingual archive displays a name in Japanese script while a small reading helps reviewers who know the spoken name but not the characters. Keep the base text in the document. The annotation supplements it; it is not a translated replacement. The fallback parentheses matter when a reader cannot present ruby annotations as intended. For an extended explanation or a full translation, use surrounding prose instead.",
    '''<p>File owner: <ruby>山田<rp>(</rp><rt>やまだ</rt><rp>)</rp></ruby>.</p>
<p>The surname is read Yamada in this record.</p>''',
    "Ruby does not supply a language translation or verify a person's preferred reading. Confirm names against the record and set document or span language appropriately when this appears inside a multilingual page.",
    "The markup adds a few nodes per annotated term. Large catalogs with annotation on every word grow the DOM and become difficult to read, so reserve it for text where the short reading helps.",
    ["Do not replace the base characters with only the annotation.", "Do not use ruby as a tooltip for paragraphs of commentary.", "Do not guess a person's name reading from spelling alone."],
    ["html/language-and-direction", "html/inline-text-meaning", "html/character-references"])

add("bidi-isolation", "semantics", "HTML bdi: isolate an unknown text direction",
    "The bdi element isolates text whose writing direction is unknown from surrounding text.",
    "A review queue includes customer names entered in several scripts. The page layout is left to right, but one name may contain right-to-left characters. Isolating each untrusted name keeps nearby punctuation and case numbers in a sensible order without forcing every name into the page direction. If a known phrase has a fixed language and direction, mark those facts directly instead of guessing from its first character.",
    '''<ul>
  <li>Case C-47 — <bdi>ليلى</bdi> — awaiting review</li>
  <li>Case C-52 — <bdi>Meera</bdi> — approved</li>
</ul>''',
    "Isolation changes text ordering behavior. It does not escape HTML, clean a submitted name, or make the application multilingual. Encode user-supplied strings before placing them inside these elements.",
    "Each isolated name adds one small element. The main cost is testing: mixed-script labels, copied text, and screen-reader output need review with real names and punctuation.",
    ["Do not use bdi as an HTML sanitizer.", "Do not force dir=ltr on a name just because the page is left to right.", "Do not omit language metadata for known-language paragraphs."],
    ["html/language-and-direction", "html/character-references", "html/inline-text-meaning"])

add("date-and-time-inputs", "forms", "HTML date and time inputs: separate display from submitted values",
    "Date and time input types provide browser controls that submit normalized value strings.",
    "A warehouse schedules a collection window for a damaged parcel. A date field records the local calendar day; a time field records a wall-clock time. Neither field identifies a timezone or resolves daylight-saving ambiguity, so the server must attach the depot's configured zone before it creates an instant. Labels state what the values mean. Boundaries should reflect operational rules, not arbitrary dates copied into a template.",
    '''<form action="/collections/schedule" method="post">
  <label for="collection-day">Collection day at the depot</label>
  <input id="collection-day" name="collection_day" type="date" min="2026-10-02" required>
  <label for="collection-time">Local pickup time</label>
  <input id="collection-time" name="collection_time" type="time" step="900" required>
  <button type="submit">Request collection</button>
</form>''',
    "The date minimum here illustrates a stated scheduling rule and must be generated from current policy on a live page. The server must reject expired dates, closed hours, and conflicting reservations regardless of browser validation.",
    "Native controls avoid a custom picker bundle. Server-side timezone conversion and availability checks still consume work, and the correct cost depends on the scheduling service rather than on the input element.",
    ["Do not treat a time value as an absolute instant.", "Do not hard-code a date bound that will expire.", "Do not rely on the browser to prevent conflicting bookings."],
    ["html/input-types", "html/form-validation", "html/time-and-machine-values"])

add("range-input-and-output", "forms", "HTML range input: capture an approximate bounded choice",
    "A range input chooses a number within defined limits; output can display a calculated or selected value.",
    "A dispatch planner sets a provisional handling priority from one through seven. A slider is suitable because the choice is approximate and the labels describe the scale; it would be a poor control for an exact invoice amount. The output below exposes the initial value in text. If client code updates the slider, it must update that output too, while the server still validates the numeric range and business rule.",
    '''<form action="/dispatch/priority" method="post">
  <label for="handling-priority">Handling priority: 1 low, 7 urgent</label>
  <input id="handling-priority" name="priority" type="range" min="1" max="7" step="1" value="4">
  <output for="handling-priority" name="priority_preview">4 of 7</output>
  <button type="submit">Save priority</button>
</form>''',
    "Output is not a substitute for the named range control. The initial output remains static unless application code synchronizes it after changes; the sample deliberately avoids pretending that behavior exists.",
    "The native slider is lightweight. Synchronizing one label takes trivial client work, while persisting priority and preventing unauthorized changes belong to the application backend.",
    ["Do not use a slider when users need an exact value.", "Do not present a stale output as a live preview.", "Do not accept a submitted value outside the server's allowed range."],
    ["html/progress-meter-output", "html/input-types", "html/form-validation"])

add("color-input", "forms", "HTML color input: collect a preference without making color the message",
    "A color input lets a user select a color value through a browser control.",
    "A team chooses an accent for its internal dashboard. The picker records a preference, while the adjacent label and preview description explain what the color will affect. Color alone must never convey whether a case is approved or held. A live application can validate contrast against its text colors and preview the result before saving, but those behaviors require code beyond the input shown here.",
    '''<form action="/teams/appearance" method="post">
  <label for="team-accent">Dashboard accent color</label>
  <input id="team-accent" name="accent" type="color" value="#315a87">
  <p>The accent marks section headings; case status remains written in text.</p>
  <button type="submit">Save appearance</button>
</form>''',
    "The server must validate the accepted color representation and reject a choice that violates product contrast rules. A color input has a value even when the user never opens its picker, so a default is a real choice.",
    "The browser supplies the picker without a third-party widget. Contrast analysis and live previews add client work if the product needs them; store the resulting preference only after server validation.",
    ["Do not use color as the only status signal.", "Do not promise a contrast-safe theme merely because the picker accepted a value.", "Do not forget that the initial color can be submitted unchanged."],
    ["html/input-types", "html/hidden-vs-aria-hidden", "html/form-validation"])

add("disabled-fieldset", "forms", "HTML disabled fieldset: stop editing without implying saved state",
    "A disabled fieldset disables most descendant form controls as one group, with a special exception for its first legend.",
    "An adjustment form opens in a locked review state. Grouping the amount and reason under one disabled fieldset prevents accidental interaction while a separate button requests unlock through a real workflow. Disabled controls are generally omitted from form submission; do not expect their current values to reach the server when another section is submitted. The server must enforce the lock independently, since a client can remove the disabled attribute.",
    '''<form action="/adjustments/A-47/review" method="post">
  <fieldset disabled>
    <legend>Adjustment A-47: locked for review</legend>
    <label for="adjustment-amount">Amount</label>
    <input id="adjustment-amount" name="amount" type="number" value="47">
    <label for="adjustment-reason">Reason</label>
    <input id="adjustment-reason" name="reason" value="Damaged parcel">
  </fieldset>
  <button type="submit" name="intent" value="request_unlock">Request unlock</button>
</form>''',
    "Only the enabled submitter contributes its intent here. The backend must re-read the stored adjustment and decide whether the caller may request an unlock; missing amount and reason fields are expected.",
    "Native disabled behavior avoids event handlers for every control. The tradeoff is discoverability and submission semantics, which require clear explanatory copy and server tests for omitted fields.",
    ["Do not use disabled as an authorization boundary.", "Do not treat omitted controls as a request to clear stored values.", "Do not disable the unlock button inside the fieldset."],
    ["html/form-names-disabled", "html/form-ownership", "html/form-validation"])

add("image-maps", "media", "HTML image maps: keep image hotspots accessible and stable",
    "An image map assigns link regions to coordinates within one image.",
    "A warehouse floor plan links two marked storage zones to their inventory pages. Each area has an action-specific text alternative, and ordinary text links repeat the destinations for people who cannot use the visual map. Coordinates are tied to the displayed image geometry; responsive scaling can break the hit targets if the map is not tested at the sizes actually shipped. A list of links is often the simpler interface when precise geometry adds little value.",
    '''<img src="/media/warehouse-zones.png" alt="Warehouse plan with north and south storage zones" usemap="#warehouse-zones" width="640" height="360">
<map name="warehouse-zones" id="warehouse-zones">
  <area shape="rect" coords="32,40,288,170" href="/inventory/north" alt="Open north zone inventory">
  <area shape="rect" coords="350,182,600,330" href="/inventory/south" alt="Open south zone inventory">
</map>
<p><a href="/inventory/north">North zone inventory</a> · <a href="/inventory/south">South zone inventory</a></p>''',
    "The image and both inventory routes must exist. Alternative text names each destination, while the image alt describes the whole plan. The duplicate text links serve as a resilient way to reach the same pages.",
    "One bitmap may be expensive on a mobile connection and the map needs viewport testing. A plain list has lower asset and maintenance cost, so keep the image only when location within the plan matters.",
    ["Do not leave an area without useful alt text.", "Do not assume fixed coordinates remain correct after responsive resizing.", "Do not make the image the only route to the linked records."],
    ["html/image-alt", "html/anchors-and-paths", "html/responsive-images"])

add("object-fallback", "media", "HTML object fallback: offer an alternate route to embedded files",
    "An object element can embed a resource and provide child content as fallback when the resource cannot be used.",
    "A quality team embeds a local PDF inspection sheet on a case page. The fallback link gives the same file to browsers that cannot display the embedded document. Keep the download link outside the object too if the team must always be able to save the file; fallback content only appears under specific conditions. The server must send the right media type and authorize access to the case document.",
    '''<h2>Inspection sheet for case C-47</h2>
<object data="/documents/C-47-inspection.pdf" type="application/pdf" width="720" height="500">
  <p>Preview unavailable. <a href="/documents/C-47-inspection.pdf">Open the inspection sheet PDF</a>.</p>
</object>
<p><a href="/documents/C-47-inspection.pdf" download="C-47-inspection.pdf">Download the PDF</a></p>''',
    "An embedded PDF is a separate viewing experience with its own controls. Object does not turn PDF text into HTML headings, make it searchable by the application, or guarantee that every browser can render it.",
    "The PDF transfer dominates page cost; embedding it may start a large request before the user needs it. Consider a descriptive link first on slow or document-heavy pages.",
    ["Do not assume fallback text is always visible.", "Do not omit a direct link when downloading is a core task.", "Do not expose private files from an unchecked static path."],
    ["html/download-links", "html/iframe-sandbox", "html/figure-and-caption"])

add("mathml-in-html", "media", "HTML MathML: keep mathematical meaning in the document",
    "MathML can represent mathematical notation as structured content inside an HTML page.",
    "A shipping-cost policy includes a formula that reviewers must inspect beside the written rule. MathML expresses the numerator, division, and comparison as a structure rather than baking the expression into an image. Surround it with prose that defines the units and rounding policy; notation alone cannot explain whether a surcharge is calculated per parcel or per shipment. Test pronunciation with the assistive technology used by the audience.",
    '''<p>Surcharge equals declared value divided by 47, rounded under the policy.</p>
<math display="block" aria-label="surcharge equals declared value divided by forty-seven">
  <mrow>
    <mi>surcharge</mi><mo>=</mo>
    <mfrac><mi>declaredValue</mi><mn>47</mn></mfrac>
  </mrow>
</math>''',
    "This expression defines a relationship, not a complete billing rule. The application must implement rounding, currencies, and policy versioning in code. The verbal label offers one reading, while the structured expression remains available to supported readers.",
    "A short formula adds little transfer weight. Complex expressions add many nodes and require authoring review; an image may look simpler but loses structure and scales less cleanly.",
    ["Do not use a formula image without an equivalent text explanation.", "Do not hide unit and rounding rules inside notation.", "Do not claim MathML executes the calculation."],
    ["html/inline-svg", "html/figure-and-caption", "html/character-references"])

add("scripting-escape-and-json", "advanced", "HTML script data: escape serialized values at the boundary",
    "A script element can carry non-executable data, but embedded strings still pass through the HTML parser.",
    "A case page ships a small JSON record for client-side display. The record ID and state are fixed here, so the sample is easy to inspect. In production, a serializer must escape any sequence that could terminate the script element, even when the JSON itself is valid. Keep the payload narrow, avoid secrets, and treat it as untrusted input after parsing; the browser's visibility is not an access-control mechanism.",
    '''<script id="case-state" type="application/json">
{"caseId":"C-47","reviewState":"pending","lineCount":3}
</script>
<main><h1>Case C-47</h1><p>Review pending.</p></main>''',
    "The data block does not run by itself. Client code must read and parse it, and the server must sanitize serialization into HTML so a stored string cannot close the script element or inject markup.",
    "Embedding a small payload can avoid one request, but it increases HTML bytes and cache coupling. Large or fast-changing data is usually easier to fetch through an authenticated endpoint.",
    ["Do not concatenate unescaped user text into a script element.", "Do not put secrets in source-visible JSON.", "Do not assume application/json prevents HTML parser termination."],
    ["html/script-loading", "html/script-modules", "html/character-references"])

add("form-associated-custom-elements", "advanced", "HTML form-associated custom elements: join the form contract deliberately",
    "A form-associated custom element can participate in form submission through ElementInternals.",
    "A dispatch system has a reusable priority picker that existing native controls cannot express well. The host below names the field and sits inside a form, but its JavaScript class must declare formAssociated, attach internals, and call setFormValue whenever the choice changes. Without that implementation, the visible custom element contributes no value to submission. Start with a native select unless the interaction and its accessibility behavior justify owning the extra code.",
    '''<form action="/dispatch/priority" method="post">
  <label for="dispatch-priority">Dispatch priority</label>
  <dispatch-priority id="dispatch-priority" name="priority"></dispatch-priority>
  <button type="submit">Save priority</button>
</form>
<script type="module">
  class DispatchPriority extends HTMLElement {
    static formAssociated = true;
    constructor() {
      super();
      this.internals = this.attachInternals();
      this.internals.setFormValue("standard");
    }
  }
  customElements.define("dispatch-priority", DispatchPriority);
</script>''',
    "The sample establishes submission wiring only; it does not draw an interactive picker. A production component needs its own keyboard behavior, accessible value, validation, reset, disabled state, and choice-update path before it can replace a select.",
    "The custom class adds script and testing cost. Native select provides value submission and keyboard behavior without that code, so compare the required interaction against the maintenance burden before choosing a custom control.",
    ["Do not assume a custom tag submits its name automatically.", "Do not ship this wiring sample as a finished picker.", "Do not skip reset, disabled, and assistive-technology tests."],
    ["html/custom-elements", "html/form-ownership", "html/select-and-textarea"])


new_paths = {"html/" + lesson[0] for lesson in lessons}
assert not new_paths.intersection(by_path)
assert all(set(lesson[-1]) <= set(by_path) | new_paths for lesson in lessons)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"html/" + lesson[0]: lesson[2] for lesson in lessons})


def make_body(lesson):
    _, _, _, definition, situation, sample, contract, cost, mistakes, related = lesson
    return (
        "<p>" + html.escape(definition) + "</p>"
        "<h2>When the element earns its place</h2><p>" + html.escape(situation) + "</p>"
        '<pre><code class="language-html">' + html.escape(sample, quote=False) + "</code></pre>"
        "<h2>Behavior boundary</h2><p>" + html.escape(contract) + "</p>"
        "<h2>Cost and operational limits</h2><p>" + html.escape(cost) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(point) + "</li>" for point in mistakes) + "</ul>"
        "<h2>Connected lessons</h2><ul>" + "".join(
            '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in related
        ) + "</ul>"
    )


by_section = {}
for index, lesson in enumerate(lessons):
    slug, section, title, definition, _, _, _, _, _, related = lesson
    path = "html/" + slug
    hub_path = "html/html-tutorial" if section == "core" else "html/html-tutorial/" + section
    hub = by_path[hub_path]
    row = copy.deepcopy(by_path["html/document-skeleton"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=title, summary=definition, body=make_body(lesson), subject=hub["subject"],
               tags=["html", section], sort_order=1600 + index,
               created_at=stamp, updated_at=stamp, published_at=stamp)
    row["data"] = {"subject_root": "html/html-tutorial", "section_path": hub_path,
                   "content_format": "html", "kind": "tutorial", "reading_minutes": 7,
                   "author_path": "authors/aitrove-editorial", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related]}
    rows.append(row)
    by_path[path] = row
    by_section.setdefault(section, []).append(path)

for section, paths in by_section.items():
    hub_path = "html/html-tutorial" if section == "core" else "html/html-tutorial/" + section
    hub = by_path[hub_path]
    hub["data"]["modules"].append({"title": "Specialized " + section + " contracts",
                                    "summary": "Focused markup choices, costs, and failure cases.", "lessons": paths})
    links = "<h2>Specialized topics</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths
    ) + "</ul>"
    hub["body"] = hub["body"].replace("<h3>Common Mistakes</h3>", links + "<h3>Common Mistakes</h3>", 1)
    hub["updated_at"] = stamp

for lesson in lessons:
    path = "html/" + lesson[0]
    target_path = lesson[-1][0]
    target = by_path[target_path]
    link = '<p><a href="/' + path + '">Related: ' + html.escape(titles[path]) + "</a>.</p>"
    if link not in target["body"]:
        target["body"] += link
        target["data"].setdefault("related", []).append({"path": path, "title": titles[path]})
        target["updated_at"] = stamp

questions = [
    ("What does the HTML doctype primarily select?", "Standards mode", "A schema download", "A JavaScript version", "The declaration influences browser rendering mode."),
    ("Does a search element create a server index?", "No", "Yes", "Only for GET forms", "The search region marks purpose; the endpoint does the searching."),
    ("Which information belongs in an article's address?", "Contact details for the article's owner", "Every postal address mentioned", "The reader's current location", "Address describes contact information for the nearest article or document."),
    ("What must remain in a ruby annotation?", "The base text", "Only the pronunciation", "A remote font", "The annotation supplements the base characters."),
    ("Does bdi sanitize user-supplied text?", "No", "Yes", "Only for right-to-left scripts", "Isolation affects text direction, not HTML escaping."),
    ("Does a time input specify a timezone?", "No", "Yes", "Only with required", "A wall-clock time needs an external timezone rule to become an instant."),
    ("Does output update automatically when a range changes?", "No", "Yes", "Only with step=1", "Client code must synchronize a displayed output after interaction."),
    ("What happens to most controls in a disabled fieldset on submit?", "Their values are omitted", "Their values are sent as empty", "They unlock on submit", "Disabled controls are not successful form controls."),
    ("What does each linked image-map area need?", "A useful alt text", "An onclick handler", "A second bitmap", "The area alternative describes the linked region's destination."),
    ("Does object fallback always appear beside a working PDF?", "No", "Yes", "Only on desktop", "Fallback content is for a resource that cannot be used."),
    ("Does MathML calculate a shipping charge?", "No", "Yes", "Only with aria-label", "MathML represents notation; application code applies billing rules."),
    ("Does a custom element submit its name merely by being inside a form?", "No", "Yes", "Only inside fieldset", "Form participation requires the form-associated custom-element contract."),
]

quiz_path = "quizzes/html-specialized-contracts"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/html-advanced-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Specialized HTML contracts quiz",
            summary="Twelve checks on document mode, forms, international text, and embedded content.",
            sort_order=3200, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["body"] = (
    "<p>Test the boundaries of specialized HTML elements before using them in a production interface.</p>"
    "<h2>Review the lessons</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in ["html/doctype-and-quirks-mode", "html/bidi-isolation", "html/date-and-time-inputs",
                     "html/image-maps", "html/mathml-in-html", "html/form-associated-custom-elements"]
    ) + "</ul><h3>Common Mistakes</h3><p>A browser control does not supply missing server policy or content verification.</p>"
)
quiz["data"]["related"] = [{"path": path, "title": titles[path]} for path in by_section["advanced"]]
quiz["data"]["questions"] = []
for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions):
    options = [correct, wrong_a, wrong_b]
    options = options[index % 3:] + options[:index % 3]
    quiz["data"]["questions"].append({"prompt": prompt, "options": options,
                                         "answer": options.index(correct), "explanation": explanation})
rows.append(quiz)
by_path[quiz_path] = quiz
quiz_hub = by_path["html/quizzes"]
quiz_hub["data"]["modules"].append({"title": quiz["title"], "summary": quiz["summary"], "lessons": [quiz_path]})
quiz_hub["body"] = quiz_hub["body"].replace(
    "</ul>", '<li><a href="/' + quiz_path + '">' + quiz["title"] + "</a></li></ul>", 1
)
by_path["html/html-tutorial"]["body"] += '<p><a href="/' + quiz_path + '">Check the specialized HTML contracts</a>.</p>'
by_path["html/html-tutorial/advanced"]["body"] += '<p><a href="/' + quiz_path + '">Check the specialized HTML contracts</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "articles and one quiz bank")

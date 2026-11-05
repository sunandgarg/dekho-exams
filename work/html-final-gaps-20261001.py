"""Add the remaining high-use HTML authoring decisions to fixture content."""

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


add("readonly-vs-disabled", "comparison", "HTML readonly versus disabled: preserve the right submission contract",
    "Readonly keeps a supported control's value in form submission; disabled removes most controls from interaction and submission.",
    "A shipment correction screen shows the registered parcel code beside an inspection note. The code is fixed for this request and still accompanies the POST, so readonly fits the visible field. A retired reference is displayed in a disabled field because it is not part of the decision. Neither attribute protects server data: a caller can change the submitted code or add a missing field. The server reads the authoritative parcel record and checks the user's permission before saving.",
    '''<form action="/shipments/S-47/review" method="post">
  <label for="parcel-code">Registered parcel code</label>
  <input id="parcel-code" name="parcel_code" value="004731" readonly>
  <label for="retired-reference">Retired reference</label>
  <input id="retired-reference" name="retired_reference" value="OLD-29" disabled>
  <label for="inspection-note">Inspection note</label>
  <textarea id="inspection-note" name="note" required></textarea>
  <button type="submit">Save review</button>
</form>''',
    "Readonly does not apply to every input type, including checkboxes. Disabled controls are omitted from successful form data. Use ordinary text when a value is only for reading and does not need control semantics.",
    "These native states need no script. The operational cost is the common backend mistake of treating a submitted readonly value as authoritative or treating an omitted disabled value as a request to clear stored data.",
    ["Do not assume readonly is a security control.", "Do not expect disabled values in the POST body.", "Do not use a disabled control when plain text communicates the record better."],
    ["html/form-names-disabled", "html/disabled-fieldset", "html/hidden-csrf-fields", "html/forms-get-post"])

add("placeholder-vs-label", "comparison", "HTML placeholder versus label: keep field identity visible",
    "A label names a form control; placeholder is a temporary input hint that can disappear as the user types.",
    "A depot search form asks for a case reference. The visible label remains present after a reference is entered, and the placeholder shows one valid shape without becoming the only instruction. A person reviewing an autofilled form should still know what each value means. If the rule needs more than a short example, place persistent help text outside the control and associate it with aria-describedby.",
    '''<form action="/cases/search" method="get">
  <label for="case-reference">Case reference</label>
  <p id="reference-format">Use the two-letter, four-digit code on your receipt.</p>
  <input id="case-reference" name="reference" placeholder="AB0047" aria-describedby="reference-format" pattern="[A-Z]{2}[0-9]{4}" required>
  <button type="submit">Find case</button>
</form>''',
    "The browser may display placeholder text differently across devices; it is not a submitted default value. The pattern is a syntax check, and the server still owns lookup and access control.",
    "A separate label and help paragraph add little markup. They reduce error and rework when a form is revisited with saved or autofilled values; relying on placeholder alone makes that state harder to read.",
    ["Do not put the only field name in placeholder.", "Do not assume placeholder text will be submitted.", "Do not confuse a matching code shape with permission to view a case."],
    ["html/form-labels", "html/form-help-and-errors", "html/input-pattern", "html/search-element"])

add("required-select-placeholder", "forms", "HTML required select: use an empty first choice when no decision exists",
    "A required single-select can use an empty-valued first option as a placeholder choice.",
    "A quality reviewer must choose a disposition for parcel P-47. If the first real option were preselected, submitting the form untouched could record a decision the reviewer never made. An empty first option keeps the field unresolved until a real choice is selected. The label states the question and the server enforces the allowed values after submission. For a decision with serious consequences, also present the parcel context and a separate confirmation step in the application.",
    '''<form action="/parcels/P-47/disposition" method="post">
  <label for="disposition">Disposition for parcel P-47</label>
  <select id="disposition" name="disposition" required>
    <option value="">Choose a disposition</option>
    <option value="hold">Hold for review</option>
    <option value="return">Return to sender</option>
    <option value="release">Release to dispatch</option>
  </select>
  <button type="submit">Continue review</button>
</form>''',
    "The empty first option is not a valid disposition. The server must reject empty and unknown values and confirm that the parcel is still eligible for the selected transition.",
    "Native select has no widget bundle. The main cost is accidental policy drift when options change in markup but the backend accepts a different set or assumes the first option is always a safe default.",
    ["Do not preselect a material decision just to avoid an empty state.", "Do not give the placeholder a real value.", "Do not rely on required for server validation."],
    ["html/select-and-textarea", "html/select-groups-and-multiple", "html/form-validation"])

add("text-input-assistance", "forms", "HTML text input assistance: keyboard hints are not validation",
    "Autocapitalize, spellcheck, and enterkeyhint influence input assistance without defining which values are valid.",
    "A technician enters an exact device serial and a free-text note. Automatic capitalization or spelling changes could corrupt the serial, while spellcheck may help with the note. The note's virtual-keyboard action can suggest sending, but the real submit button remains visible. These hints vary across browsers and input methods; a physical keyboard may ignore them. The server validates the serial against a record rather than trusting any keyboard behavior.",
    '''<form action="/devices/lookup" method="post">
  <label for="device-serial">Device serial</label>
  <input id="device-serial" name="serial" autocapitalize="off" spellcheck="false" required>
  <label for="device-note">Technician note</label>
  <textarea id="device-note" name="note" spellcheck="true" enterkeyhint="done"></textarea>
  <button type="submit">Check device</button>
</form>''',
    "The browser may ignore a hint, and none of these attributes blocks pasted or programmatically submitted text. A live form should preserve the typed value after a server error.",
    "Native hints cost a few bytes and no dependency. The failure cost is subtle data corruption if a serial is silently changed or if a team assumes the keyboard action replaces a visible submit control.",
    ["Do not treat autocapitalize=off as normalization.", "Do not hide the submit button because enterkeyhint is present.", "Do not enable spell correction for exact identifiers."],
    ["html/autocomplete-and-inputmode", "html/input-types", "html/form-labels"])

add("lazy-iframe-loading", "media", "HTML lazy iframe: delay an optional embedded view",
    "Loading=lazy on an iframe asks the browser to defer its navigation until the frame approaches the viewport.",
    "An inspection report offers an optional read-only map beneath the written address and route instructions. The main report remains useful before the map loads, and a normal link offers an alternate way to open it. Give the frame a title and stable dimensions so late loading does not shift nearby content. Lazy loading should be measured on the real page; a frame placed at the top may be needed immediately and gain little from deferral.",
    '''<section>
  <h2>Depot approach</h2>
  <p>Use the north gate for inspection I-47.</p>
  <iframe src="/maps/depot-north" title="North gate depot map" loading="lazy" width="640" height="360"></iframe>
  <p><a href="/maps/depot-north">Open the depot map as a page</a></p>
</section>''',
    "The map route must exist and any private coordinates need server authorization. Lazy is a browser loading policy, not a sandbox, privacy boundary, or guarantee that no bytes are requested before scrolling.",
    "Deferral can save a frame document, script, and map assets for readers who never reach this section. The fixed size reduces layout shift but reserves space even when the frame fails.",
    ["Do not lazy-load a frame needed for the first screen without measurement.", "Do not omit a useful title.", "Do not depend on the iframe as the only route to the map."],
    ["html/iframe-sandbox", "html/iframe-permissions", "html/image-loading-priority"])

add("script-import-maps", "advanced", "HTML import maps: resolve a module name to a controlled local file",
    "An import map gives the browser rules for resolving module specifiers in module scripts.",
    "A case dashboard imports a small local chart module by a stable name. The map keeps that name independent from the file path, but it does not install packages, bundle dependencies, or verify the chart's output. Serve the referenced file with an appropriate JavaScript media type and place the map before a module that relies on its rule. A build tool may already rewrite imports, so use this mechanism when native browser resolution is a deliberate deployment choice.",
    '''<script type="importmap">
{
  "imports": {
    "case-chart": "/assets/case-chart-v47.mjs"
  }
}
</script>
<script type="module">
  import { renderCaseChart } from "case-chart";
  renderCaseChart(document.querySelector("#case-chart"));
</script>
<div id="case-chart"><p>Case chart loads when scripting is available.</p></div>''',
    "The local module must exist and export renderCaseChart. If the import or render fails, users still need an accessible text summary of the underlying case data; the placeholder alone is not such a summary.",
    "The map is small, but the imported module and its graph add network and execution cost. Measure them separately and avoid a chart for data that a short table can present more clearly.",
    ["Do not place a required import map after modules resolve.", "Do not assume a mapped file exists because the JSON parses.", "Do not make the chart the only representation of case data."],
    ["html/script-modules", "html/noscript-fallback", "html/data-tables"])

add("meta-description", "core", "HTML meta description: write a page summary from actual content",
    "A meta description is document metadata that can supply a short summary to consumers of the page.",
    "A public depot policy page has a specific title and one-sentence description that match the visible heading and opening paragraph. This is a summary, not an instruction that a search engine must display it verbatim or rank the page. For a private case detail, avoid placing personal information in metadata that may be copied into previews, logs, or sharing tools. Generate descriptions from published content rather than stale template labels.",
    '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Depot west parcel inspection policy</title>
  <meta name="description" content="How depot west records seal checks and handles parcels awaiting inspection.">
</head>
<body><main><h1>Depot west parcel inspection policy</h1>
  <p>Record the seal code before deciding whether a parcel can leave the depot.</p>
</main></body>
</html>''',
    "The description is not visible body copy by itself. Keep the displayed policy and its metadata aligned after edits; the server and publishing system control which document is public.",
    "The tag has negligible load cost. The maintenance cost is editorial drift when thousands of pages inherit a generic description instead of a short, accurate summary of their current content.",
    ["Do not put private case data in a public page description.", "Do not reuse one generic description for every route.", "Do not claim the metadata controls search results."],
    ["html/metadata-title", "html/document-skeleton", "html/headings-and-paragraphs"])

add("aria-current-navigation", "accessibility", "HTML aria-current: mark the current page within a link set",
    "Aria-current identifies the item that represents the present location in a related set.",
    "A case record offers Summary, Evidence, and Decision links. On the Summary page, the Summary link is marked current, while the others remain ordinary destinations. That state should be derived from the active route, not hard-coded into a shared navigation template. Keep the visible treatment consistent with the programmatic state and leave the link text meaningful without an icon or color cue.",
    '''<nav aria-label="Case C-47 sections">
  <ul>
    <li><a href="/cases/C-47" aria-current="page">Summary</a></li>
    <li><a href="/cases/C-47/evidence">Evidence</a></li>
    <li><a href="/cases/C-47/decision">Decision</a></li>
  </ul>
</nav>
<main><h1>Case C-47 summary</h1><p>Evidence review is pending.</p></main>''',
    "Only the current link gets aria-current=page in this set. The markup does not route requests or authorize access to evidence and decisions; those pages need real handlers and server checks.",
    "One attribute costs almost nothing. The maintenance risk is stale current state after route changes, especially in templates reused for several record types or nested paths.",
    ["Do not mark two pages current in one navigation set.", "Do not depend on color alone to show current location.", "Do not let a shared template freeze the current state on the wrong route."],
    ["html/landmarks", "html/anchors-and-paths", "html/skip-link"])

add("multiple-email-input", "forms", "HTML multiple email input: parse a list, not a single address",
    "An email input with multiple accepts a comma-separated list of email addresses for one named control.",
    "A service desk invites several depot contacts to one maintenance update. The field label says multiple addresses are allowed and the visible help states how to separate them. A browser syntax check can reject malformed entries, but it cannot confirm that an address belongs to the intended person, prevent a typo from contacting someone else, or establish consent to send a message. The server must split, normalize, and apply its own recipient-count policy before dispatch.",
    '''<form action="/updates/maintenance/invite" method="post">
  <label for="recipient-emails">Depot contacts to invite</label>
  <p id="recipient-help">Separate addresses with commas; maximum three recipients.</p>
  <input id="recipient-emails" name="recipients" type="email" multiple required aria-describedby="recipient-help">
  <button type="submit">Review invitations</button>
</form>''',
    "The stated maximum of three is a server rule; multiple by itself does not impose it. The next page should show the parsed recipients before any external message is sent.",
    "The native control is light. Recipient parsing, deduplication, consent checks, and error handling are the real work, especially when a malformed entry appears in the middle of a list.",
    ["Do not assume multiple sets a recipient-count limit.", "Do not send invitations solely after browser syntax validation.", "Do not hide the comma-separation rule in placeholder text."],
    ["html/input-types", "html/form-help-and-errors", "html/form-validation"])


new_paths = {"html/" + lesson[0] for lesson in lessons}
assert len(lessons) == 9 and not new_paths.intersection(by_path)
assert all(set(lesson[-1]) <= set(by_path) | new_paths for lesson in lessons)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"html/" + lesson[0]: lesson[2] for lesson in lessons})


def body_for(lesson):
    _, _, _, definition, case, sample, boundary, cost, mistakes, links = lesson
    return (
        "<p>" + html.escape(definition) + "</p>"
        "<h2>Why this choice matters</h2><p>" + html.escape(case) + "</p>"
        '<pre><code class="language-html">' + html.escape(sample, quote=False) + "</code></pre>"
        "<h2>What it does not do</h2><p>" + html.escape(boundary) + "</p>"
        "<h2>Cost and operational limits</h2><p>" + html.escape(cost) + "</p>"
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
               tags=["html", section], sort_order=2200 + index,
               created_at=stamp, updated_at=stamp, published_at=stamp)
    row["data"] = {"subject_root": "html/html-tutorial", "section_path": hub_path,
                   "content_format": "html", "kind": "tutorial", "reading_minutes": 7,
                   "author_path": "authors/aitrove-editorial", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in links]}
    rows.append(row)
    by_path[path] = row
    by_section.setdefault(section, []).append(path)

for section, paths in by_section.items():
    hub_path = "html/html-tutorial" if section == "core" else "html/html-tutorial/" + section
    hub = by_path[hub_path]
    hub["data"]["modules"].append({"title": "Practical " + section + " distinctions",
                                    "summary": "Native browser behavior and application responsibilities.",
                                    "lessons": paths})
    additions = "<h2>Practical distinctions</h2><ul>" + "".join(
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

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "articles")

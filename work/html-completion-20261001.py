"""Fill distinct HTML metadata, text, form, media, and disclosure gaps."""

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


add("viewport-metadata", "core", "HTML viewport metadata: let a mobile layout use device width",
    "The viewport meta declaration advises mobile browsers how to size the layout viewport.",
    "A field technician opens an inspection record on a phone. With width=device-width, a responsive stylesheet can size the record against the device viewport rather than a wide virtual canvas. This tag does not itself make a two-column desktop layout usable on a narrow screen. The content order, controls, tables, and CSS still need mobile review. Avoid disabling zoom: technicians may need to enlarge a dense serial number or inspection note.",
    '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Inspection I-47</title>
</head>
<body><main><h1>Inspection I-47</h1><p>Seal check pending.</p></main></body>
</html>''',
    "The declaration belongs in head. It does not set actual text size, replace responsive CSS, or guarantee that large tables fit. Test zoom, landscape orientation, and keyboard focus on real narrow viewports.",
    "The metadata adds negligible transfer weight. The expensive mistakes are layout overflow and controls that require horizontal scrolling; those are design and implementation costs outside this tag.",
    ["Do not set user-scalable=no to conceal a broken layout.", "Do not assume device width makes fixed-width content responsive.", "Do not omit the title while tuning mobile behavior."],
    ["html/document-skeleton", "html/metadata-title", "html/data-tables"])

add("site-icon-metadata", "core", "HTML site icon: identify a document in browser UI",
    "A link with the icon relationship supplies a candidate image for browser tabs and related interface surfaces.",
    "A dispatch console has a small mark that should remain recognizable beside many open tabs. The head points to a same-site icon asset, while the title carries the precise record identity because a tiny image cannot communicate a queue number. Keep the asset stable and test it on light and dark browser chrome. An icon is branding, not an accessible replacement for the document title or the main heading.",
    '''<head>
  <meta charset="utf-8">
  <title>Dispatch queue — depot west</title>
  <link rel="icon" href="/assets/depot-mark.svg" type="image/svg+xml">
</head>''',
    "The file must be deployed at the specified local path and served with the expected media type. Browsers may cache icons aggressively, so a changed file can appear stale until its URL or cache state changes.",
    "A compact icon adds one small request that may be cached across pages. A huge source image wastes bytes and may still look poor when reduced to tab size.",
    ["Do not depend on an icon to name the page.", "Do not point to an asset absent from deployment.", "Do not assume a browser instantly refreshes a cached icon."],
    ["html/metadata-title", "html/resource-hints", "html/image-alt"])

add("data-element-values", "semantics", "HTML data element: pair visible labels with machine values",
    "The data element associates human-readable text with a machine-readable value.",
    "An inventory page names a part in prose while retaining its stable stock code in markup. The code is useful to a script or extractor, but it is not a substitute for a proper database key in the backend. If the value is a date or time, use time instead so the temporal meaning is explicit. The displayed name remains what a person reads, even if the internal identifier changes between systems.",
    '''<p>Replacement part: <data value="bearing-47B">sealed bearing</data>.</p>
<p>Warehouse slot: <data value="west-aisle-9">West aisle, shelf nine</data>.</p>''',
    "Data does not fetch a record or enforce that the code exists. A server response must keep the visible label and value consistent with the same inventory state; client code should not trust a value copied from another page.",
    "The element is light. The maintenance cost lies in keeping machine identifiers stable and reconciling them after catalog migrations, not in rendering two short spans of markup.",
    ["Do not use data to hide sensitive identifiers from a page visitor.", "Do not place a date in data when time expresses it better.", "Do not let the label and value describe different parts."],
    ["html/time-and-machine-values", "html/inline-text-meaning", "html/global-attributes"])

add("ins-and-del", "semantics", "HTML ins and del: show an edit without falsifying current text",
    "The ins and del elements identify inserted and removed content in a document revision.",
    "A service policy changes its inspection threshold. Keeping the old and new phrases in the change view lets a reviewer understand the edit. The datetime attributes record when the change was made; a visible sentence still explains what the current policy is for readers who do not inspect element semantics. Once the change is accepted into the main policy, a clean current version may be easier to read than permanent inline revision marks.",
    '''<p>Inspection threshold changed on 1 October 2026:
  <del datetime="2026-10-01">45 minutes</del>
  <ins datetime="2026-10-01">47 minutes</ins>.
</p>
<p>The current threshold is 47 minutes.</p>''',
    "The markup records a textual change, not an audit trail. The server must retain who approved the revision, what version it replaced, and any legal or operational evidence required by the product.",
    "Two extra elements cost almost nothing. Large documents with every historical edit inline become hard to scan, so separate a concise current policy from a dedicated change log when revisions accumulate.",
    ["Do not use del merely to make text look crossed out.", "Do not confuse a timestamp with approval evidence.", "Do not leave the current rule ambiguous between old and new values."],
    ["html/time-and-machine-values", "html/inline-text-meaning", "html/sections-and-articles"])

add("word-break-opportunities", "semantics", "HTML wbr: suggest a break inside an unbroken identifier",
    "The wbr element marks a position where the browser may break a long string onto another line.",
    "A narrow audit panel displays a generated shipment reference that has no spaces. Adding a possible break after its fixed prefix keeps the identifier readable without changing the characters that users copy. The browser may choose another break based on available width. If a code must remain one unbroken unit for machine parsing, store and transmit its original value independently rather than scraping text from a rendered panel.",
    '''<p>Shipment reference:
  <code>WEST47-<wbr>DEPOT19-<wbr>REVIEW204</code>
</p>''',
    "A soft break is a layout opportunity, not a delimiter in the business identifier. The code remains the same sequence of visible characters; test selection, copy, and screen-reader reading for the intended audience.",
    "Wbr adds tiny DOM overhead. It cannot repair a container with a fixed width or a design that clips overflow, so check the complete page at mobile sizes.",
    ["Do not insert spaces that alter an identifier's meaning.", "Do not expect wbr to force a line break at every width.", "Do not use it to conceal a broader overflow problem."],
    ["html/inline-text-meaning", "html/viewport-metadata", "html/character-references"])

add("input-pattern", "forms", "HTML pattern: validate a field's syntax without claiming identity",
    "The pattern attribute constrains the syntax of certain text-like input values during browser validation.",
    "A depot asks for a local six-character claim reference: two uppercase letters followed by four digits. The visible label and description give users the rule; the pattern mirrors it as a client-side check. A syntactically valid reference can still be nonexistent, belong to another account, or be expired. The server must verify those facts and repeat the syntax check, because clients can bypass or change their own markup.",
    '''<form action="/claims/lookup" method="get">
  <label for="claim-reference">Claim reference, two letters and four digits</label>
  <input id="claim-reference" name="reference" type="text" pattern="[A-Z]{2}[0-9]{4}" title="Use two capital letters followed by four digits" required>
  <button type="submit">Find claim</button>
</form>''',
    "The expression describes the whole value under HTML pattern matching. It does not normalize lowercase text or remove pasted spaces; decide whether the product should transform input before checking it.",
    "Browser matching is cheap for this bounded expression. Complicated patterns cost authoring and testing time, can yield poor error messages, and still do not replace server-side record lookup.",
    ["Do not use a successful pattern match as authorization.", "Do not place the only rule explanation in title.", "Do not write an expression whose accepted values differ from server policy."],
    ["html/form-validation", "html/form-labels", "html/character-references"])

add("input-length-limits", "forms", "HTML length limits: bound user text and explain the stored rule",
    "Minlength and maxlength express length constraints for supported text controls.",
    "A maintenance ticket asks for a concise fault summary. The limits tell the browser what to accept, while the label states the length range in plain language. Character counting can differ from a backend byte limit, especially with non-ASCII text and emoji. A product that stores this value in a database needs a server-side length policy with a clear definition and an error message that returns the user's text rather than discarding it.",
    '''<form action="/tickets/new" method="post">
  <label for="fault-summary">Fault summary, 12 to 160 characters</label>
  <textarea id="fault-summary" name="summary" minlength="12" maxlength="160" required></textarea>
  <button type="submit">Create ticket</button>
</form>''',
    "These attributes constrain a browser control, not a database column. The server should validate the incoming text under the same product rule and protect against oversized requests independently.",
    "Bounding a short summary reduces accidental large submissions. The control itself is cheap; useful validation feedback and consistent Unicode handling take more care than the two attributes.",
    ["Do not assume a database byte count equals the browser's character count.", "Do not discard text after a server rejection.", "Do not set a maximum without explaining it to the user."],
    ["html/form-validation", "html/select-and-textarea", "html/form-labels"])

add("form-dirname", "forms", "HTML dirname: submit text direction beside the user's words",
    "The dirname attribute asks a form submission to include the direction of a text control in a separate named field.",
    "An international support form accepts a customer explanation in either writing direction. Recording that direction can help a downstream case viewer render the note as intended. The text itself still needs escaping, a visible label, and a server-side policy for storing language and direction metadata. Direction is not the same as language, and a reported direction is not proof of the author's identity or locale.",
    '''<form action="/support/cases" method="post">
  <label for="case-explanation">Explain the damaged shipment</label>
  <textarea id="case-explanation" name="explanation" dirname="explanation_dir" dir="auto" required></textarea>
  <button type="submit">Send case</button>
</form>''',
    "The submitted fields include explanation and explanation_dir. The latter is a direction token, not a translation or a language tag; validate and store it alongside the note if the application needs it.",
    "The additional field adds little transfer cost. Handling mixed-direction text correctly across storage, logs, exports, and later rendering is the substantial implementation work.",
    ["Do not infer the user's language from explanation_dir.", "Do not trust submitted direction metadata without validation.", "Do not insert the explanation into HTML without escaping."],
    ["html/language-and-direction", "html/bidi-isolation", "html/form-names-disabled"])

add("select-groups-and-multiple", "forms", "HTML optgroup and multiple select: make several choices explicit",
    "Optgroup labels related options; a select with multiple permits more than one selected value.",
    "A dispatch supervisor assigns a job to two or more service areas. The field name makes repeated submitted values visible to the backend, while grouped options shorten scanning through the area list. Native multiple-selection gestures vary by device, so explain them and test a phone before committing to this interface. If several choices are central to the task, a clearly labeled checkbox group may be easier to operate.",
    '''<form action="/dispatch/areas" method="post">
  <label for="service-areas">Service areas; select every area involved</label>
  <select id="service-areas" name="area" multiple size="5" required>
    <optgroup label="North depot">
      <option value="north-loading">Loading</option>
      <option value="north-inspection">Inspection</option>
    </optgroup>
    <optgroup label="South depot">
      <option value="south-packing">Packing</option>
      <option value="south-dispatch">Dispatch</option>
    </optgroup>
  </select>
  <button type="submit">Save service areas</button>
</form>''',
    "The server must accept and validate repeated area values, reject unknown codes, and enforce any limit on selections. Optgroup provides a label for a set of choices; it does not submit its own value.",
    "The HTML is small. The usability cost of a native multiple select can be high on touch devices, so compare it with checkboxes using the real choice count and target devices.",
    ["Do not parse repeated values as one comma-separated string by accident.", "Do not assume users know the modifier key for multiple selection.", "Do not expect an optgroup label in submitted data."],
    ["html/select-and-textarea", "html/radio-checkbox", "html/form-labels"])

add("exclusive-details-groups", "accessibility", "HTML details name groups: open one disclosure at a time",
    "Details elements sharing a nonempty name form a group in which at most one disclosure is open.",
    "A short equipment checklist has three mutually exclusive instruction panels. The group keeps only one long procedure visible, saving space on a handheld screen. That choice has a cost: a technician comparing two procedures cannot keep both open. If comparison is common, independent details elements or ordinary headings are better. Use a real summary for each panel and place related disclosures together under one heading.",
    '''<section>
  <h2>Equipment inspection steps</h2>
  <details name="inspection-steps" open>
    <summary>Check the seal</summary><p>Record the seal code before opening the crate.</p>
  </details>
  <details name="inspection-steps">
    <summary>Measure the package</summary><p>Use the calibrated depot scale.</p>
  </details>
  <details name="inspection-steps">
    <summary>Release the package</summary><p>Confirm the signed inspection note.</p>
  </details>
</section>''',
    "Only one member starts open. The browser handles the disclosure state, but it does not complete an inspection, save a checklist, or prevent a technician from skipping a panel.",
    "This is a native interaction with no application bundle. The main cost is task friction when users need simultaneous panels; test the workflow before choosing exclusivity.",
    ["Do not set open on two details in the same name group.", "Do not use a disclosure as a substitute for required form validation.", "Do not group panels that users need to compare side by side."],
    ["html/dialog-and-details", "html/focus-and-native-controls", "html/viewport-metadata"])

add("iframe-permissions", "media", "HTML iframe allow: grant an embedded page only needed capabilities",
    "An iframe allow attribute declares a permissions policy for selected features in the embedded document.",
    "A trusted local scanning tool is embedded in a parcel intake page and needs camera access. The parent permits that capability for the frame. The browser may still ask the user for permission, and the framed page must be served by a route the team controls. The allow list is not a guarantee that camera capture works, nor a replacement for server authorization of uploaded scans.",
    '''<iframe src="/tools/parcel-scan" title="Parcel barcode scanner" width="480" height="360"
  allow="camera"></iframe>
<p>If the scanner is unavailable, enter the parcel code in the intake form.</p>''',
    "This example assumes the scanner is a trusted part of the same application. An untrusted scanner needs a separate origin and a carefully designed sandbox and permissions policy. Review the exact trust boundary before embedding one.",
    "Camera access and embedded scripts have device and memory costs. Defer loading when scanning is optional, and measure the framed tool separately from the parent page.",
    ["Do not treat allow as automatic user consent.", "Do not embed untrusted code at a trusted application route.", "Do not make the camera the only way to enter a parcel code."],
    ["html/iframe-sandbox", "html/iframe-srcdoc-boundary", "html/form-labels"])

add("video-poster-preload", "media", "HTML video poster and preload: control the first-screen transfer",
    "Video poster supplies an image before playback, while preload hints how much media data to fetch early.",
    "An inspection archive includes a recording below the case summary. A poster gives the reader a relevant still without requiring immediate video playback, and preload=none avoids pulling the full recording just because the page opened. Controls remain available to start it. The recording and poster still need owned assets, useful surrounding context, and a text alternative for information the video conveys.",
    '''<h2>Inspection I-47 recording</h2>
<video controls preload="none" poster="/media/I-47-still.webp" width="640" height="360">
  <source src="/media/I-47-recording.mp4" type="video/mp4">
  <p>Video playback unavailable. Request the inspection transcript from the case team.</p>
</video>''',
    "Preload is a hint, not a strict byte cap. The browser may fetch metadata or ignore the requested policy under some conditions. A poster is not a transcript, and the fallback paragraph is not timed captioning.",
    "The poster adds an image request, usually smaller than the video. Measure total page transfer and lazy loading on the actual archive route; a large poster can erase the benefit of deferring video data.",
    ["Do not autoplay an evidence recording by default.", "Do not assume preload=none guarantees zero media bytes.", "Do not treat a still frame as an accessible alternative to the recording."],
    ["html/video-captions", "html/video-source-fallback", "html/image-loading-priority"])

add("video-track-languages", "media", "HTML track languages: label subtitles and captions honestly",
    "Track elements attach timed text files to a media element and identify each track's kind and language.",
    "A safety briefing has the original spoken English, English captions that include non-speech sound, and a translated Hindi subtitle file. Their labels tell viewers which track they are choosing. Provide one appropriate default rather than marking every track default. The files must actually contain synchronized cues; the HTML tag does not transcribe audio, translate dialogue, or audit caption quality.",
    '''<video controls preload="metadata" width="640" height="360">
  <source src="/media/safety-briefing-47.mp4" type="video/mp4">
  <track kind="captions" src="/media/safety-briefing-47.en.vtt" srclang="en" label="English captions" default>
  <track kind="subtitles" src="/media/safety-briefing-47.hi.vtt" srclang="hi" lang="hi" label="हिन्दी">
  <p>Video playback unavailable. Read the briefing transcript in the safety section.</p>
</video>''',
    "The two local WebVTT paths need real, tested files. Captions and subtitles serve different needs; an inaccurately labeled translation can mislead users who expect descriptions of sound.",
    "Timed text files are usually small beside video, but synchronization and translation review take real editorial work. Test track selection, cue timing, and text contrast on supported browsers.",
    ["Do not mark multiple caption or subtitle tracks as default.", "Do not label translated dialogue as sound-complete captions.", "Do not publish a track pointing to a missing VTT file."],
    ["html/video-captions", "html/video-poster-preload", "html/language-and-direction"])

add("hidden-until-found", "advanced", "HTML hidden until found: let search reveal deferred text",
    "The hidden=until-found state hides content while allowing browser find-in-page or fragment navigation to reveal it.",
    "A long audit report keeps a technical appendix collapsed from the initial reading path, yet a reviewer searching for a specific sensor model should still reach that text. The heading has an ID for direct navigation. This is a visibility state, not secure storage: the content remains in the delivered document and is available to scripts and anyone reading source. Test browser support and styles; some display rules can prevent the reveal behavior.",
    '''<main>
  <h1>Inspection I-47</h1>
  <p>The sensor details are available in the technical appendix.</p>
  <section id="sensor-appendix" hidden="until-found">
    <h2>Sensor appendix</h2>
    <p>Model SR-47 was calibrated before the seal check.</p>
  </section>
  <p><a href="#sensor-appendix">Open the sensor appendix</a></p>
</main>''',
    "A supporting browser may reveal the section for the fragment or a text match. The state does not create a keyboard-operated disclosure control for every user; use details if manual open and close is the main task.",
    "The hidden text still increases HTML transfer and DOM size. For a very large appendix, a separate document may be cheaper than shipping all content on every report view.",
    ["Do not place confidential text in a hidden section.", "Do not apply display:none when reveal behavior is required.", "Do not assume the state replaces an explicit disclosure control."],
    ["html/hidden-and-inert", "html/anchors-and-paths", "html/dialog-and-details"])


new_paths = {"html/" + lesson[0] for lesson in lessons}
assert len(lessons) == 14
assert not new_paths.intersection(by_path)
assert all(set(lesson[-1]) <= set(by_path) | new_paths for lesson in lessons)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"html/" + lesson[0]: lesson[2] for lesson in lessons})


def body_for(lesson):
    _, _, _, definition, case, sample, boundary, cost, mistakes, links = lesson
    return (
        "<p>" + html.escape(definition) + "</p>"
        "<h2>Use it in a concrete workflow</h2><p>" + html.escape(case) + "</p>"
        '<pre><code class="language-html">' + html.escape(sample, quote=False) + "</code></pre>"
        "<h2>Behavior and ownership</h2><p>" + html.escape(boundary) + "</p>"
        "<h2>Performance and maintenance</h2><p>" + html.escape(cost) + "</p>"
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
               tags=["html", section], sort_order=1800 + index,
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
    hub["data"]["modules"].append({"title": "Further " + section + " decisions",
                                    "summary": "Browser contracts with explicit server and accessibility boundaries.",
                                    "lessons": paths})
    additions = "<h2>Further decisions</h2><ul>" + "".join(
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

questions = [
    ("What does width=device-width change?", "The layout viewport sizing hint", "The page's text size", "The server's image dimensions", "Viewport metadata affects the mobile layout viewport, not the CSS itself."),
    ("Can a site icon replace a page title?", "No", "Yes", "Only on mobile", "A tiny icon cannot identify a document as precisely as title text."),
    ("What does data value provide?", "A machine-readable counterpart to visible text", "A database lookup", "A private field", "The value is embedded metadata and is visible in the document."),
    ("Do ins and del create an approval audit trail?", "No", "Yes", "Only with datetime", "Revision markup does not store approver identity or workflow evidence."),
    ("Does wbr alter the underlying shipment reference?", "No", "Yes", "Only when copied", "It marks a possible visual line break without adding a separator."),
    ("Does a valid pattern prove a claim exists?", "No", "Yes", "Only for GET", "Syntax validation and record lookup are separate operations."),
    ("Can a backend byte limit be assumed equal to maxlength?", "No", "Yes", "Only with ASCII labels", "Browser text length and stored byte length can differ."),
    ("What does dirname submit beside a note?", "Its text direction", "Its language translation", "Its author identity", "The extra field records a direction token."),
    ("Does optgroup send its label as a selected value?", "No", "Yes", "Only with multiple", "Only selected options supply values."),
    ("What does a shared details name do?", "Allows at most one panel open", "Submits all panels", "Creates modal behavior", "Members of the same details name group are mutually exclusive."),
    ("Does iframe allow=camera guarantee camera access?", "No", "Yes", "Only when sandboxed", "Permissions policy does not replace browser permission or device support."),
    ("Does preload=none guarantee zero media transfer?", "No", "Yes", "Only with a poster", "Preload is a browser hint rather than a byte guarantee."),
]

quiz_path = "quizzes/html-markup-decisions"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/html-specialized-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="HTML markup decisions quiz",
            summary="Twelve explained checks on metadata, text, forms, disclosures, and media.",
            sort_order=3300, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["body"] = (
    "<p>Choose markup by the actual browser behavior, then check what still belongs to the application.</p>"
    "<h2>Review the decisions</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in ["html/viewport-metadata", "html/data-element-values", "html/input-pattern",
                     "html/form-dirname", "html/exclusive-details-groups", "html/video-track-languages"]
    ) + "</ul><h3>Common Mistakes</h3><p>Keep browser hints separate from server validation and ownership of files.</p>"
)
quiz["data"]["related"] = [{"path": path, "title": titles[path]} for path in by_section["forms"]]
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
by_path["html/html-tutorial"]["body"] += '<p><a href="/' + quiz_path + '">Check HTML markup decisions</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "articles and one quiz bank")

"""Add practical HTML form, accessibility, and resource decisions to fixtures."""

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
lessons = []


def add(slug, section, title, definition, case, sample, boundary, cost, mistakes, links):
    lessons.append((slug, section, title, definition, case, sample, boundary, cost, mistakes, links))


add("button-type-default", "forms", "HTML button type: make every form action explicit",
    "A button inside a form can submit that form when its type is omitted; type=button is for an action that does not submit.",
    "A reviewer can open a short policy note while filling an inspection report. That disclosure must not send the unfinished report, so its button declares type=button and targets a native popover. The final action declares type=submit. This distinction matters after a template change: moving an untyped button into a form can silently turn a harmless-looking control into a submission trigger. The server still treats a submitted report as untrusted input and checks the reviewer's permission.",
    '''<form action="/inspections/I-47/reports" method="post">
  <label for="seal-note">Seal inspection note</label>
  <textarea id="seal-note" name="note" required></textarea>
  <button type="button" popovertarget="seal-policy">Read seal policy</button>
  <button type="submit">Submit inspection report</button>
</form>
<div id="seal-policy" popover><p>Record a broken seal before dispatch.</p></div>''',
    "The popover button changes local interface state; it does not save data. Explicit button types also clarify intent for maintainers, but they do not prevent duplicate POST requests or replace backend idempotency where it is needed.",
    "Native button and popover behavior require no widget dependency. The main cost of an omitted type is accidental submission, which can waste a user's work or create duplicate records if the backend is not defensive.",
    ["Do not leave a non-submit button's type implicit inside a form.", "Do not use type=button for the actual form submission unless script submits it deliberately.", "Do not mistake a disabled submit button for a server-side duplicate-request guard."],
    ["html/link-vs-button", "html/native-popover", "html/forms-get-post"])

add("dialog-form-method", "advanced", "HTML form method=dialog: close a decision panel without a network request",
    "A form whose method is dialog closes its containing dialog when a submit button is activated, without sending form data to an action URL.",
    "An incident reviewer opens a panel to read a hold explanation, then closes it and returns to the unfinished report. The close action belongs to the dialog's local interaction, not to the incident API. The button's value can identify the selected close action to script through the dialog return value, but nothing in this markup persists a hold. If accepting a decision changes a record, put that request in a separate authorized flow with a visible confirmation and a real server endpoint.",
    '''<button type="button" id="open-hold-note">Read hold note</button>
<dialog id="hold-note">
  <h2>Why this parcel is held</h2>
  <p>The seal code on the intake record needs a second check.</p>
  <form method="dialog">
    <button type="submit" value="close">Return to report</button>
  </form>
</dialog>
<script>
  const holdNote = document.querySelector("#hold-note");
  document.querySelector("#open-hold-note").addEventListener("click", () => holdNote.showModal());
</script>''',
    "The dialog method is meaningful only when the form is inside a dialog. Closing a panel is not the same as approving a business decision. Focus and Escape-key behavior should be checked in the actual browser interface.",
    "The browser supplies modal behavior and focus containment without a custom overlay library. Script is still needed here to open the dialog; a custom implementation would add more event and focus-management work.",
    ["Do not expect method=dialog to POST data.", "Do not present a close button as though it saved an incident decision.", "Do not open a modal dialog without checking its focus order and close path."],
    ["html/dialog-and-details", "html/dialog-vs-popover", "html/focus-order-tabindex"])

add("file-accept-hint", "forms", "HTML file accept: guide the picker, validate the upload on the server",
    "The accept attribute hints which file types a file picker should offer; it is not a security or content-validation boundary.",
    "An intake team attaches up to four scanned delivery slips as PDF files. The picker hint reduces accidental image uploads, while the visible help states the intended format and count. The server must enforce the limit, inspect actual content, cap bytes, and store files outside executable paths. A file with a PDF name can contain unexpected data, and a client can bypass the picker entirely. The form uses multipart encoding because binary files need a submission format that can carry them.",
    '''<form action="/intake/I-47/slips" method="post" enctype="multipart/form-data">
  <label for="delivery-slips">Delivery slips</label>
  <p id="slip-rules">Attach up to four PDF files, no more than 8 MB each.</p>
  <input id="delivery-slips" name="slips" type="file" accept=".pdf,application/pdf" multiple required aria-describedby="slip-rules">
  <button type="submit">Upload slips</button>
</form>''',
    "Neither accept nor multiple imposes the four-file or size limit. The example route needs a real upload handler, authorization, and a safe storage policy before deployment.",
    "The picker hint adds no script. Server-side content inspection and storage are the real costs; skipping them turns a convenience attribute into a false security assumption.",
    ["Do not trust the extension or client-declared media type.", "Do not assume accept blocks every unwanted selection.", "Do not omit multipart/form-data for a normal file-upload form."],
    ["html/file-upload-form", "html/form-validation", "html/form-help-and-errors"])

add("password-autocomplete-tokens", "forms", "HTML password autocomplete: distinguish current and new credentials",
    "Autocomplete tokens identify the purpose of a credential field so the browser can offer appropriate stored values.",
    "A staff sign-in form asks for an account name and the current password. Naming the fields username and current-password helps password managers offer the correct secret, rather than treating a change-password field as a login field. On a password reset form, use new-password for the replacement secret; one-time-code belongs to a separate verification code field. These hints are about autofill semantics. The server still authenticates the account, limits abuse, and protects the session after login.",
    '''<form action="/staff/session" method="post">
  <label for="staff-account">Staff account</label>
  <input id="staff-account" name="username" autocomplete="username" required>
  <label for="staff-secret">Current password</label>
  <input id="staff-secret" name="password" type="password" autocomplete="current-password" required>
  <button type="submit">Sign in</button>
</form>''',
    "A password input hides typed characters on screen; it does not encrypt transport or make client-side validation trustworthy. Autocomplete behavior can vary by browser and password manager, and the form needs HTTPS in any real deployment.",
    "The markup is tiny. Correct field semantics can reduce failed logins and password-reset confusion, while the operational cost lies in the authentication service and its security controls.",
    ["Do not label a replacement secret current-password.", "Do not disable useful password-manager behavior to conceal a broken form.", "Do not treat type=password as a substitute for HTTPS and server authentication."],
    ["html/autocomplete-and-inputmode", "html/input-types", "html/form-labels"])

add("print-stylesheet-media", "core", "HTML print stylesheet: declare a separate rendering context",
    "A stylesheet link with media=print applies its CSS when the document is printed or shown in print preview.",
    "An inspection report has navigation and action controls on screen, but the printed record needs a legible heading, dates, and evidence summary without those controls. The print stylesheet can hide chrome and tune page breaks while the HTML keeps one semantic source of truth. Treat print as a different presentation of the same record, not as a private export path: anyone who can access the page can inspect its markup. A printable report still needs server authorization and a stable record snapshot if it is used as evidence.",
    '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Inspection I-47 report</title>
  <link rel="stylesheet" href="/assets/report-screen.css">
  <link rel="stylesheet" href="/assets/report-print.css" media="print">
</head>
<body>
  <main><h1>Inspection I-47</h1><p>Seal check recorded before dispatch.</p></main>
</body>
</html>''',
    "Media selection governs application of styles, not access control. Browsers may still fetch a nonmatching stylesheet, so do not claim that media=print removes all network cost from screen views.",
    "A second CSS file adds maintenance and may add a request. It is usually cheaper than duplicating report markup, provided print preview is tested whenever the underlying document layout changes.",
    ["Do not build a separate printable page that drifts from the report data.", "Do not assume print CSS keeps private content hidden.", "Do not forget to test page breaks and long tables in print preview."],
    ["html/document-skeleton", "html/metadata-title", "html/data-tables"])

add("image-decoding-hint", "media", "HTML image decoding: choose a paint hint without promising speed",
    "The decoding attribute expresses a preference for how the browser decodes an image before painting it.",
    "A long inspection record contains a photograph below the written finding. The photograph can load near the viewport and decode asynchronously, allowing text to appear while the bitmap is prepared. Its width and height reserve a predictable box so that late arrival does not push the report around. This is a measured choice, not a blanket rule for every image: a hero visual or a critical diagram may need a different priority strategy, and decoding does not determine when the bytes are downloaded.",
    '''<figure>
  <img src="/images/inspection-I-47-seal.webp" alt="Seal on parcel I-47 with a split along the upper edge" width="960" height="640" loading="lazy" decoding="async">
  <figcaption>Seal condition at intake, before dispatch.</figcaption>
</figure>''',
    "The browser may honor or ignore the decoding preference. Async decode can allow non-image content to paint first; it does not reduce file size, repair an inaccurate alt text, or guarantee better Core Web Vitals.",
    "This hint adds almost no markup cost. The image itself dominates bytes and memory, so correct dimensions, compression, source selection, and placement matter more than the hint alone.",
    ["Do not confuse decoding=async with loading=lazy.", "Do not lazy-load a critical first-screen image without measuring the result.", "Do not omit dimensions when the image size is known."],
    ["html/image-loading-priority", "html/responsive-images", "html/image-alt"])

add("textarea-wrap-submission", "forms", "HTML textarea wrap: distinguish display wrapping from submitted line breaks",
    "Textarea wrap=soft changes how text is displayed, while wrap=hard can insert line breaks into the submitted value using the declared column width.",
    "An incident narrative should preserve the editor's intentional line breaks, so soft wrapping is appropriate. A separate fixed-width export note feeds a legacy print system that expects short lines, making hard wrapping a deliberate integration contract. Keep these fields distinct. A CSS width can change how the control looks without changing the form value; hard wrapping changes that value. If exact bytes matter, test the browser-to-server payload rather than inferring it from the visual line breaks.",
    '''<form action="/incidents/I-47/notes" method="post">
  <label for="incident-narrative">Incident narrative</label>
  <textarea id="incident-narrative" name="narrative" rows="7" wrap="soft" required></textarea>
  <label for="print-note">Fixed-width print note</label>
  <textarea id="print-note" name="print_note" rows="4" cols="36" wrap="hard"></textarea>
  <button type="submit">Save notes</button>
</form>''',
    "Hard wrapping requires cols and its line-breaking details are browser-defined. The server should normalize and validate text for the receiving system rather than relying on a particular visual wrap location.",
    "Soft wrapping has no extra processing cost. Hard wrapping can alter stored text and diffs; use it only when the downstream format needs inserted line breaks, not merely to make an editor narrower.",
    ["Do not use wrap=hard just to control on-screen width.", "Do not assume CSS line wrapping changes submitted text.", "Do not compare unnormalized line endings across systems."],
    ["html/select-and-textarea", "html/form-dirname", "html/form-validation"])

add("aria-invalid-errors", "accessibility", "HTML aria-invalid: connect a failed field to a repair instruction",
    "Aria-invalid identifies a control whose current value failed validation; an associated message explains how to repair it.",
    "A server rejects a case reference after a search request because the value has the wrong format. The response returns the submitted value, marks only that field invalid, and puts a plain-language repair instruction beside it. The instruction has an id used by aria-describedby, so the field and the reason stay connected. This state belongs to a failed submission, not to an untouched form. For a full-page response, also provide a visible error summary near the top when several controls fail.",
    '''<form action="/cases/search" method="get">
  <label for="case-lookup">Case reference</label>
  <input id="case-lookup" name="reference" value="C47" aria-invalid="true" aria-describedby="case-lookup-error" required>
  <p id="case-lookup-error">Enter two letters followed by four digits, such as CD0047.</p>
  <button type="submit">Search cases</button>
</form>''',
    "Aria-invalid communicates state; it does not run validation or prevent submission. The server must still check syntax, permission, and whether the case exists. Remove the invalid state after the user corrects the value or after a successful response.",
    "One attribute and a message have negligible load cost. The main maintenance cost is keeping error state, text, and actual validation rule aligned across client and server rendering.",
    ["Do not mark every empty required field invalid before interaction.", "Do not show only a red border with no repair text.", "Do not leave aria-invalid=true after the error has cleared."],
    ["html/form-help-and-errors", "html/form-validation", "html/required-vs-aria-required"])

add("draft-formnovalidate", "forms", "HTML formnovalidate: save a draft without publishing incomplete data",
    "A submit button with formnovalidate skips browser constraint validation for that submission only.",
    "A field inspector can save a report before writing the final finding, while publication requires that finding. The draft button posts to a draft endpoint and bypasses the required-field check; the publish button uses the form action and normal browser validation. The backend must keep these operations separate. Draft storage may accept incomplete fields, but publishing must run full server validation and permission checks regardless of which button or endpoint a client claims to use.",
    '''<form action="/reports/R-47/publish" method="post">
  <label for="final-finding">Final finding</label>
  <textarea id="final-finding" name="finding" required></textarea>
  <button type="submit" formaction="/reports/R-47/draft" formnovalidate>Save draft</button>
  <button type="submit">Publish report</button>
</form>''',
    "Formnovalidate affects native browser checks; it does not disable validation implemented by script or server. A draft is still a state-changing request and needs authentication, authorization, and request protection.",
    "The attribute costs nothing in delivery. The real engineering cost is a clear state model so incomplete drafts cannot accidentally become public records through a forged or misrouted request.",
    ["Do not let the publish endpoint trust browser validation.", "Do not treat a draft POST as harmless because required was bypassed.", "Do not send both buttons to one ambiguous backend action without an explicit decision."],
    ["html/submit-button-overrides", "html/form-validation", "html/hidden-csrf-fields"])

add("submitter-name-value", "forms", "HTML submitter value: identify which button sent the form",
    "Only the submit button used to initiate a form submission contributes its name and value to the submitted entry list.",
    "A case list has two search scopes: unresolved and archived. Both buttons submit the same query field, but the activated button supplies the requested scope. This avoids a hidden field that script must rewrite before every submit. The server still checks that the scope belongs to an allowed set and applies access rules for archived records. Pressing Enter can trigger an implicit submission path, so place the intended default action first and test keyboard behavior on the actual form.",
    '''<form action="/cases" method="get">
  <label for="case-query">Search case records</label>
  <input id="case-query" name="query" type="search">
  <button type="submit" name="scope" value="unresolved">Unresolved cases</button>
  <button type="submit" name="scope" value="archived">Archived cases</button>
</form>''',
    "The browser does not submit every button's value. A programmatic form submission may have no button value unless a submitter is specified, so the server must define a safe default for missing scope.",
    "Native submitter values replace a small amount of client script. The backend branching remains, and GET query strings should contain only information suitable for URLs, history, and logs.",
    ["Do not expect both scope values in one request.", "Do not treat a missing scope as an authorization grant.", "Do not put private case details in a GET query."],
    ["html/forms-get-post", "html/submit-button-overrides", "html/form-names-disabled"])

add("autofocus-dialog", "accessibility", "HTML autofocus in a dialog: put focus on the next useful action",
    "Autofocus identifies the element that should receive focus when its containing dialog is shown.",
    "An operator opens a small correction panel containing a readonly asset code and an editable reason. Focusing the readonly code would make the next step unclear; the reason field is the useful starting point. Keep the dialog heading and context visible, then choose one autofocus target within that dialog. The opener must remain available so focus can return when the panel closes. For long or destructive dialogs, the safest first focus target may be the dialog or a non-destructive control instead of the confirm button.",
    '''<button type="button" id="open-correction">Correct inspection</button>
<dialog id="correction-panel" aria-labelledby="correction-heading">
  <h2 id="correction-heading">Correct inspection I-47</h2>
  <form action="/inspections/I-47/corrections" method="post">
    <label for="correction-reason">Reason for correction</label>
    <textarea id="correction-reason" name="reason" autofocus required></textarea>
    <button type="submit">Review correction</button>
  </form>
</dialog>
<script>
  const correctionPanel = document.querySelector("#correction-panel");
  document.querySelector("#open-correction").addEventListener("click", () => correctionPanel.showModal());
</script>''',
    "Autofocus is a focus request, not a substitute for an accessible dialog name, visible labels, or backend validation. Only one element in the same autofocus scope should carry the attribute.",
    "Native dialog focus behavior avoids hand-written trapping code. The remaining cost is interaction testing across keyboard and assistive technology combinations, especially after conditional fields are added.",
    ["Do not autofocus the destructive confirmation by default.", "Do not put multiple autofocus targets in one dialog.", "Do not assume focus placement proves the form is accessible."],
    ["html/dialog-and-details", "html/focus-order-tabindex", "html/form-labels"])

add("linked-image-alt", "accessibility", "HTML linked image alt: name the destination or avoid repetition",
    "The alternative text for an image used as a link should convey the link's purpose when the image provides its only name.",
    "A case evidence tile links to a scan. If the scan thumbnail is the entire link, its alt text names the destination rather than listing visual details irrelevant to navigation. If visible link text already says the same thing, the thumbnail can use an empty alt to avoid repeating the name. The full evidence page still needs a useful description of the scan itself; a thumbnail's link label cannot carry every fact in the document.",
    '''<p><a href="/cases/C-47/evidence/seal-scan"><img src="/images/C-47-seal-thumb.webp" alt="Open seal scan for case C-47" width="240" height="160"></a></p>
<p><a href="/cases/C-47/evidence/log"><img src="/images/C-47-log-icon.webp" alt="" width="32" height="32"> Open intake log for case C-47</a></p>''',
    "A broken image still needs a usable link name. The destination route must exist and enforce access to case evidence; descriptive alt text is not an access control or a replacement for a document transcript.",
    "Good alternatives add only a few words. The real cost is editorial upkeep when a thumbnail's destination changes but its link name does not, causing misleading navigation for nonvisual users.",
    ["Do not leave an image-only link with empty alt text.", "Do not repeat visible link text verbatim in a decorative thumbnail's alt.", "Do not use filenames as the link's accessible name."],
    ["html/image-alt", "html/anchors-and-paths", "html/figure-and-caption"])


new_paths = {"html/" + lesson[0] for lesson in lessons}
assert len(lessons) == 12 and not new_paths.intersection(by_path)
assert all(set(lesson[-1]) <= set(by_path) | new_paths for lesson in lessons)
titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"html/" + lesson[0]: lesson[2] for lesson in lessons})


def body_for(lesson):
    _, _, _, definition, case, sample, boundary, cost, mistakes, links = lesson
    return (
        "<p>" + html.escape(definition) + "</p>"
        "<h2>When it earns its place</h2><p>" + html.escape(case) + "</p>"
        '<pre><code class="language-html">' + html.escape(sample, quote=False) + "</code></pre>"
        "<h2>Browser boundary</h2><p>" + html.escape(boundary) + "</p>"
        "<h2>Cost and maintenance</h2><p>" + html.escape(cost) + "</p>"
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
               tags=["html", section], sort_order=2300 + index,
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
    hub["data"]["modules"].append({"title": "Production " + section + " decisions",
                                    "summary": "Native browser behavior, accessible interaction, and server boundaries.",
                                    "lessons": paths})
    additions = "<h2>Production decisions</h2><ul>" + "".join(
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

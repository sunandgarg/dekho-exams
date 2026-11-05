"""Add focused HTML lessons where the first curriculum pass left common gaps."""

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


# Definition, operational case, markup, boundary, cost, mistakes, related routes.
drafts = [
    ("global-attributes", "core", "HTML global attributes: keep id, class, and data-* jobs separate",
     "Global attributes apply across HTML elements, but id, class, and data-* answer different questions.",
     "A receipt row needs a fragment target, a styling hook, and a small client-side identifier. The id is unique in this document and can be addressed by a link or label. A class may be shared across many rows. A data attribute carries application state into the DOM, but it must never be trusted as proof of access rights or as the source of record truth.",
     '''<section id="receipt-r47" class="receipt-card" data-receipt-id="R-47">
  <h2>Receipt R-47</h2>
  <p>Awaiting finance review.</p>
</section>
<a href="#receipt-r47">Jump to receipt R-47</a>''',
     "The fragment link reaches an existing id. CSS can select the class, and a script can read the data value if behavior is later added. The server still chooses which receipt is visible; changing a DOM attribute cannot authorize a request.",
     "These attributes add little markup weight. Duplicate ids, however, break label and fragment relationships; duplicating state in data attributes can also drift from the rendered text.",
     ["Do not repeat an id on several cards.", "Do not use a class as the target of a label's for attribute.", "Do not put a secret in data-* because page source is public to the client."],
     ["html/anchors-and-paths", "html/form-labels", "html/character-references"]),
    ("inline-text-meaning", "core", "HTML inline text: emphasis, importance, code, and abbreviations",
     "Inline text elements mark a change in meaning inside a sentence without inventing a new page section.",
     "A receipt review notice contains an operational warning, a command, and a shortened technical term. Strong importance belongs on the warning, code identifies the literal command, and abbr expands a short label. An em element would mark stress in the sentence; it is not a generic italic styling hook. The surrounding paragraph remains ordinary prose and can be read without CSS.",
     '''<p><strong>Export is blocked</strong> until the receipt is approved.</p>
<p>Run <code>receipts verify R-47</code> against the test ledger.</p>
<p>The <abbr title="service-level agreement">SLA</abbr> is 47 hours.</p>
<p><em>Only</em> approved receipts enter the export batch.</p>''',
     "The elements carry meaning even when a stylesheet changes their default appearance. A code element identifies literal text, not a runnable command; the example command requires a real tool before anyone can execute it.",
     "Inline semantics have negligible runtime cost. The maintenance cost lies in claiming emphasis or importance where the content does not warrant it, which makes long pages noisy to scan.",
     ["Do not use strong for every visually bold word.", "Do not treat a code label as proof that a command exists.", "Use CSS when the only goal is visual italic or bold styling."],
     ["html/headings-and-paragraphs", "html/character-references", "html/html-tags-a-to-z-list"]),
    ("quotes-and-citations", "semantics", "HTML quotations: keep quoted text and attribution distinct",
     "A blockquote holds a longer quotation, while q marks a short quotation within running text.",
     "The finance team keeps an approval policy excerpt beside a receipt. The quotation is the policy language; the attribution names the owning team without pretending that a cite attribute is displayed as a visible credit. The example uses a local policy route only if that route exists in the application. Short quoted terms in a paragraph use q, allowing the user agent to handle quotation marks.",
     '''<figure>
  <blockquote>
    <p>Export records after the second reviewer confirms the batch.</p>
  </blockquote>
  <figcaption>Finance review policy, revision 47</figcaption>
</figure>
<p>The policy calls this state <q>confirmed for export</q>.</p>''',
     "The figure caption provides a visible attribution. An external legal or policy claim still needs a verifiable owner and revision in the real application; HTML semantics do not authenticate quoted content.",
     "A quotation needs only a few elements. The costly error is editorial: stale policy text can mislead reviewers even when the markup is technically valid.",
     ["Do not use blockquote merely to indent prose.", "Do not assume cite supplies visible attribution.", "Keep policy wording and revision synchronized with the actual owner."],
     ["html/figure-and-caption", "html/sections-and-articles", "html/time-and-machine-values"]),
    ("input-types", "forms", "HTML input types: choose controls from the value contract",
     "An input type selects a browser control and may add type-specific validation, but it never defines the server contract alone.",
     "A finance contact form collects a reply address and a whole-number batch count. The email type requests email-shaped input. A number control expresses a numeric quantity with a minimum and step; it is a poor choice for a receipt ID, where leading zeros and letters are meaningful. The server parses and bounds both fields again because requests can bypass the browser.",
     '''<form action="/finance/contact" method="post">
  <label for="reply-address">Reply address</label>
  <input id="reply-address" name="reply_address" type="email" required>
  <label for="batch-count">Batch count</label>
  <input id="batch-count" name="batch_count" type="number" min="1" max="47" step="1" required>
  <button type="submit">Send request</button>
</form>''',
     "The endpoint must exist and validate each value according to its business meaning. Browser error messages can help a user correct input, but they are neither authorization nor an anti-abuse boundary.",
     "Native controls avoid custom parsing UI. They still require tests for empty input, decimals, exponent forms, locale display, and values outside the allowed range at the server boundary.",
     ["Do not use type=number for identifiers or postal codes.", "Do not trust min and max as server-side validation.", "Keep names stable because submitted entries use name, not id."],
     ["html/form-validation", "html/form-names-disabled", "html/forms-get-post"]),
    ("autocomplete-and-inputmode", "forms", "HTML autocomplete and inputmode: describe purpose and keyboard hints",
     "autocomplete names the value a field expects; inputmode suggests an input interface without changing the field's data type.",
     "A review form asks for the reviewer's email and a numeric reference code. Email is a meaningful field purpose, so the browser can offer a stored address where appropriate. The reference remains text because leading zeros matter; inputmode hints at a numeric keyboard on touch devices, but a physical keyboard and pasted text still work. Both values are checked by the receiving service.",
     '''<form action="/receipts/lookup" method="post">
  <label for="reviewer-email">Reviewer email</label>
  <input id="reviewer-email" name="email" type="email" autocomplete="email">
  <label for="reference-code">Reference code</label>
  <input id="reference-code" name="reference" type="text" inputmode="numeric" pattern="[0-9]{6}">
  <button type="submit">Find receipt</button>
</form>''',
     "The numeric keyboard is a hint, not a lock. The six-character pattern describes the client constraint, while the endpoint must handle malformed, missing, and unauthorized references. The POST body still needs transport security and careful handling of personal data in logs.",
     "No script is needed for these hints. The network and privacy costs belong to the form submission and its backend, so keep collected fields limited to what the lookup needs.",
     ["Do not confuse inputmode with input validation.", "Do not set autocomplete values that misdescribe the field.", "Do not log private form values without an operational need."],
     ["html/input-types", "html/forms-get-post", "html/form-validation"]),
    ("datalist-suggestions", "forms", "HTML datalist: offer suggestions without closing the input",
     "A datalist offers candidate values to a compatible input while leaving the user free to enter another value.",
     "An operations form suggests common receipt categories, yet some legitimate entries are new. The input's list attribute points to the datalist id. Each option is a suggestion, not a validated enumeration, and the server stores only categories that meet the application's rules. If the values must be restricted, a select element is a better contract than an open text field.",
     '''<form action="/receipts/category" method="post">
  <label for="category-name">Receipt category</label>
  <input id="category-name" name="category" list="category-options" required>
  <datalist id="category-options">
    <option value="Travel">
    <option value="Equipment">
    <option value="Facilities">
  </datalist>
  <button type="submit">Save category</button>
</form>''',
     "The datalist id is a relationship target, not a field name. Browser presentation can differ; the plain input remains useful when suggestions are not shown. The endpoint and permitted category policy are application responsibilities.",
     "A short local list costs little. Hundreds of options make the document heavy and are hard to scan; search-backed suggestions then need a real service and an accessible interaction design.",
     ["Do not treat a datalist suggestion as an enforced option.", "Do not confuse the datalist id with the submitted input name.", "Use select when the choice really is closed."],
     ["html/select-and-textarea", "html/form-names-disabled", "html/form-validation"]),
    ("progress-meter-output", "forms", "HTML progress, meter, and output: three different value relationships",
     "progress represents task completion, meter represents a measured value in a known range, and output represents a calculation result.",
     "A receipt job has completed 29 of 47 records. A separate confidence score is 0.82 on a zero-to-one scale. These are not interchangeable: progress communicates work remaining, while meter communicates a gauge. The output shows a computed amount; its value must be updated by application code or supplied by the server, because HTML does not perform the calculation.",
     '''<p>Export completion: <progress value="29" max="47">29 of 47</progress></p>
<p>Match confidence: <meter min="0" max="1" value="0.82">0.82</meter></p>
<form action="/receipts/estimate" method="get">
  <label for="receipt-total">Receipt total</label>
  <input id="receipt-total" name="total" type="number" min="0" step="0.01">
  <output for="receipt-total" name="estimate">Awaiting calculation</output>
  <button type="submit">Calculate</button>
</form>''',
     "The output text here is a placeholder until the endpoint returns a result. Keep a visible text equivalent for the meter's meaning and avoid assuming every browser draws these controls in the same way.",
     "Native indicators have little client cost. The backend cost is tracking accurate task state; stale numbers are a product defect even with correct HTML.",
     ["Do not use progress as a generic score gauge.", "Do not imply output calculates automatically.", "Do not omit the max when a determinate task has a defined total."],
     ["html/form-validation", "html/select-and-textarea", "html/receipt-review-form-project"]),
    ("form-ownership", "forms", "HTML form ownership: connect an external submit button deliberately",
     "A form-associated control can name its owner through the form attribute even when it appears outside that form's subtree.",
     "A sticky action bar may sit after the main form in the DOM so it is reached after the fields. Giving the submit button form=review-form associates it with the correct form. This is an HTML relationship, not a CSS relationship. If a page has several forms, explicit ownership prevents a button from submitting whichever form happens to enclose it after a layout change.",
     '''<form id="review-form" action="/receipts/review" method="post">
  <label for="decision-note">Decision note</label>
  <textarea id="decision-note" name="note" required></textarea>
</form>
<section aria-label="Review action">
  <button type="submit" form="review-form">Submit review</button>
</section>''',
     "The service endpoint still authenticates the reviewer and validates note length. The form attribute only selects which controls participate in native submission; it does not create a server handler or move the button into the form's DOM subtree.",
     "This avoids a JavaScript submit proxy and its event and focus edge cases. The price is maintaining one unique form id and verifying that future refactors do not separate the button from its intended task order.",
     ["Do not use an id that appears on several forms.", "Do not set type=button when native submission is intended.", "Do not assume visual adjacency determines form ownership."],
     ["html/forms-get-post", "html/form-labels", "html/focus-and-native-controls"]),
    ("audio-controls", "media", "HTML audio: give recorded guidance native controls and a transcript",
     "The audio element embeds an audio resource; controls requests a browser playback interface.",
     "An operations page carries a short recorded explanation of the receipt workflow. A text transcript follows the player so the information remains available without sound, when playback fails, or when a user would rather scan than listen. The source path represents an owned media file; it must exist and be served with an appropriate type. The browser chooses what it can play.",
     '''<section aria-labelledby="guide-heading">
  <h2 id="guide-heading">Review workflow guide</h2>
  <audio controls preload="metadata">
    <source src="/media/review-guide-47.mp3" type="audio/mpeg">
    Your browser cannot play this recording.
  </audio>
  <details>
    <summary>Read the transcript</summary>
    <p>Verify the receipt ID, review the amount, then record the decision.</p>
  </details>
</section>''',
     "The fallback sentence is shown when audio itself is unsupported; a playable file can still fail to load. The transcript must match the final recording, and any spoken instructions that change require the text to change too.",
     "Media bytes dominate the cost. Preloading metadata usually avoids requesting the full recording immediately, but network behavior still depends on the user agent and server response.",
     ["Do not autoplay spoken guidance without a user request.", "Do not publish a player without the referenced asset.", "Do not use a transcript that omits instructions heard in the audio."],
     ["html/video-captions", "html/dialog-and-details", "html/figure-and-caption"]),
    ("template-inert-markup", "accessibility", "HTML template: stage inert markup before a script clones it",
     "A template holds markup that is parsed but not rendered as live page content until a script inserts a clone.",
     "A receipt interface may need to add rows after a response arrives. The template stores the row shape without showing a fake record on first render. Its placeholders are not data: a script must clone the fragment, fill text safely, and append it to a real list. If scripting fails, the page still needs a useful empty state or server-rendered records.",
     '''<ul id="receipt-results">
  <li>No receipts loaded yet.</li>
</ul>
<template id="receipt-row-template">
  <li><span class="receipt-id"></span> — <span class="receipt-state"></span></li>
</template>''',
     "The template does not loop, fetch, or escape values by itself. When code fills it, assign untrusted strings as text rather than interpreting them as HTML. Remove the empty-state row only after actual results are ready.",
     "An unused template is inexpensive markup but adds bytes. Inserted records create DOM nodes proportional to results, so paginate or virtualize very large lists only when measurements justify that complexity.",
     ["Do not expect template contents to appear automatically.", "Do not insert server text with innerHTML without a trusted parser and sanitization policy.", "Do not remove fallback content before data successfully arrives."],
     ["html/script-loading", "html/character-references", "javascript/getting-started"]),
]


for index, (slug, section, title, definition, scenario, code, consequence, cost, mistakes, links) in enumerate(drafts):
    path = "html/" + slug
    assert path not in by_path, path
    assert all(target in by_path for target in links), (path, links)
    hub_path = "html/html-tutorial" if section == "core" else "html/html-tutorial/" + section
    hub = by_path[hub_path]
    body = "<p>" + html.escape(definition) + "</p>"
    body += "<h2>Use it for a real task</h2><p>" + html.escape(scenario) + "</p>"
    body += '<pre><code class="language-html">' + html.escape(code, quote=False) + "</code></pre>"
    body += "<h2>What the markup guarantees</h2><p>" + html.escape(consequence) + "</p>"
    body += "<h2>Cost and limits</h2><p>" + html.escape(cost) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(m) + "</li>" for m in mistakes) + "</ul>"
    body += "<h2>Connected lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(by_path[target]["title"]) + "</a></li>" for target in links
    ) + "</ul>"
    row = copy.deepcopy(by_path["html/document-skeleton"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=title, summary=definition, body=body, subject=hub["subject"],
               tags=["html", section], sort_order=1200 + index,
               created_at=stamp, updated_at=stamp, published_at=stamp)
    row["data"] = {"subject_root": "html/html-tutorial", "section_path": hub_path,
                   "content_format": "html", "kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "seo_ready": True,
                   "related": [{"path": target, "title": by_path[target]["title"]} for target in links]}
    rows.append(row)
    by_path[path] = row
    hub["data"]["modules"].append({"title": title, "summary": definition, "lessons": [path]})
    hub["body"] += '<p><a href="/' + path + '">' + html.escape(title) + "</a>. " + html.escape(definition) + "</p>"
    # Keep the new subject matter discoverable from the nearest prior lesson.
    prior = by_path[links[0]]
    prior["body"] += '<p><a href="/' + path + '">Continue with ' + html.escape(title) + "</a>.</p>"
    prior["data"].setdefault("related", []).append({"path": path, "title": title})

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(drafts), "HTML depth lessons")

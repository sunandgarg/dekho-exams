"""Expand the element reference and connect focused semantic lessons."""

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


def linked(paths):
    return "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    )


def add_article(path, title, summary, intro, explanation, sample, cost, mistakes, related):
    assert path not in by_path
    body = (
        "<p>" + intro + "</p><h2>Use the distinction</h2><p>" + explanation + "</p>"
        '<pre><code class="language-html">' + html.escape(sample, quote=False) + "</code></pre>"
        "<h2>Behavior and cost</h2><p>" + cost + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + item + "</li>" for item in mistakes) + "</ul>"
        "<h2>Connected lessons</h2><ul>" + linked(related) + "</ul>"
    )
    template = by_path["html/quotes-and-citations"]
    entry = copy.deepcopy(template)
    entry.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path, title=title, summary=summary, body=body,
        subject=by_path["html/html-tutorial/semantics"]["subject"],
        tags=["html", "semantics"], sort_order=4000 + len(rows),
        created_at=stamp, updated_at=stamp, published_at=stamp,
    )
    entry["data"] = {
        "subject_root": "html/html-tutorial", "section_path": "html/html-tutorial/semantics",
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


add_article(
    "html/mark-relevant-text",
    "HTML mark: identify relevant text without calling it a warning",
    "Use mark for context-dependent relevance and strong for actual importance.",
    "The mark element identifies text relevant to the reader's current task. It does not say the author originally emphasized that text or that the text is a warning.",
    "A case search returns a sentence containing the matched seal term. The result page can mark the match so a reader locates it quickly. A separate strong message communicates that dispatch is blocked. The result still needs a readable title, case link, and surrounding context when highlight styling is absent. On a longer excerpt, highlight only the matching words; marking an entire paragraph erases the distinction. If the search term comes from a request, escape it as text before inserting any markup. The server must not allow a query to become raw HTML in the result.",
    '''<main>
  <h1>Case search results</h1>
  <article>
    <h2><a href="/cases/C-47">Case C-47</a></h2>
    <p>The upper <mark>seal</mark> was split during intake.</p>
    <p><strong>Dispatch blocked until review.</strong></p>
  </article>
</main>''',
    "Native markup costs no script. Search highlighting still needs safe text matching, correct escaping, and a result service; a static mark tag cannot find matches on its own. Check the result in high contrast and without CSS, since a color change alone may not convey why a word is highlighted. If assistive-technology users need an explicit match count, provide that in ordinary text. Avoid using mark as generic yellow styling for unrelated copy.",
    ["Do not replace a warning's importance with mark merely because the default paint is bright.", "Do not insert unescaped query text into a result fragment.", "Do not highlight every word in a passage and call that a search match."],
    ["html/inline-text-meaning", "html/search-form-contract", "html/character-references"],
)

add_article(
    "html/br-and-hr-boundaries",
    "HTML br and hr: separate a line from a change of subject",
    "Use br for a meaningful line break and hr for a paragraph-level thematic break.",
    "A br element inserts a line break within text. An hr element marks a thematic break between passages. Neither is a spacing control for layout.",
    "A printed collection address has meaningful line boundaries, so line breaks help preserve its postal form. Below it, a new paragraph changes from collection instructions to an exception policy. That change can justify a thematic separator if the surrounding headings do not already make the shift clear. Ordinary paragraphs should usually remain paragraphs; inserting repeated br elements to force a visual gap makes source order harder to maintain and can sound strange when read aloud. A heading is preferable when the next passage begins a named section that readers should find by heading navigation.",
    '''<main>
  <h1>Collection notice</h1>
  <p>Return damaged parcels to:<br>
     Bay 47<br>
     North depot<br>
     Harbour Road</p>
  <p>Attach the intake record before the collection window closes.</p>
  <hr>
  <p>If the seal is open, hold the parcel for a supervisor instead.</p>
</main>''',
    "Both elements are tiny and need no script. The cost is editorial misuse: an hr cannot create a new section hierarchy, and br cannot make a list or address relationship that is not present in the words. CSS owns margins and borders. Test the page with styles disabled and at narrow widths; the breaks should still match the text's intended meaning. If the separator adds no meaning beyond a visual rule, put that rule in CSS rather than in the document.",
    ["Do not stack br elements to simulate paragraph margins.", "Do not insert hr between every section when headings already express the division.", "Do not use a visible line as the only cue for a changed instruction."],
    ["html/headings-and-paragraphs", "html/address-contact-info", "html/sections-and-articles"],
)

add_article(
    "html/kbd-samp-var",
    "HTML kbd, samp, and var: separate input, output, and variables",
    "Mark typed commands, system responses, and replaceable values by their roles.",
    "The kbd element identifies user input, samp identifies sample computer output, and var identifies a variable or placeholder. Code identifies code, which is a different role.",
    "An operations note asks a reviewer to type a command using a case ID supplied by the current record. The command itself is user input; the case identifier is a replaceable value. The response line is a sample result, not another command to paste. Put any safety condition in prose before the snippet, especially if a real tool could change records. The example below is explanatory markup: the named command is not supplied by this lesson. If a product has a real command-line workflow, publish its precise permission model and verified output separately.",
    '''<main>
  <h1>Inspect a case state</h1>
  <p>In an authorized test environment, type
    <kbd>case-inspect --id <var>case_id</var></kbd>.
    Replace <var>case_id</var> with the current record ID.</p>
  <p>A successful test may return <samp>Case C-47: held</samp>.</p>
  <p>The response is sample output; it is not proof of a live case.</p>
</main>''',
    "These text elements add almost no transfer cost. The real maintenance work is keeping command examples synchronized with an actual tool, avoiding secrets in pasted output, and telling readers which fragments are literal. A syntax highlighter is optional; it does not replace the input-output distinction. Test copy-and-paste instructions carefully: a reader should not have to guess whether angle brackets, identifiers, or punctuation are part of the command. If an example could be destructive, state the environment and authorization boundary before it.",
    ["Do not mark a program's response as something the user should type.", "Do not present a placeholder as a literal production identifier.", "Do not invent a command and imply it exists in the deployed application."],
    ["html/preformatted-code-and-output", "html/inline-text-meaning", "html/character-references"],
)


reference = by_path["html/html-tags-a-to-z-list"]
reference["title"] = "HTML elements by purpose: a practical reference"
reference["summary"] = "A working index of document, text, form, table, media, and component elements."
groups = [
    ("Document and metadata", [
        ("html", "Root of an HTML document; set its language when known."),
        ("head", "Metadata and resource declarations, before rendered content."),
        ("title", "The document name used in tabs, history, and many search displays."),
        ("meta", "Character encoding and other named document metadata."),
        ("link", "Document relationships and resource declarations such as stylesheets."),
        ("base", "A document-wide base for resolving relative references; use carefully."),
        ("style", "A stylesheet embedded in the document."),
        ("body", "The document's rendered content."),
    ], ["html/document-skeleton", "html/metadata-title", "html/color-scheme-metadata"]),
    ("Page regions and headings", [
        ("header", "Introductory material for a page or a section."),
        ("nav", "A major group of navigation links."),
        ("main", "The page's dominant content."),
        ("article", "A composition that stands on its own, such as a case report."),
        ("section", "A named subdivision of related content."),
        ("aside", "Content related to the main flow but not part of it."),
        ("footer", "Closing material for a page or section."),
        ("search", "A region containing a search interface."),
        ("address", "Contact details for the nearest article or the page."),
        ("h1–h6", "Heading ranks; use the level that matches the real hierarchy."),
        ("hgroup", "A heading grouped with subordinate heading content."),
    ], ["html/landmarks", "html/sections-and-articles", "html/search-form-contract"]),
    ("Blocks, lists, and changes of topic", [
        ("p", "A paragraph of prose."),
        ("div", "A grouping container when no more specific element fits."),
        ("hr", "A thematic change between passages, not a decorative border."),
        ("pre", "Text whose spacing and line breaks carry structure."),
        ("blockquote", "A longer quotation from another source."),
        ("ol", "A sequence where order matters."),
        ("ul", "A collection without a required order."),
        ("menu", "A list of commands or actions."),
        ("li", "One member of an ordered, unordered, or menu list."),
        ("dl", "A set of terms and their descriptions."),
        ("dt", "A term in a description list."),
        ("dd", "The corresponding description or value."),
        ("figure", "Self-contained content that can be referred to as one unit."),
        ("figcaption", "A caption for a figure."),
    ], ["html/lists-and-definitions", "html/br-and-hr-boundaries", "html/figure-and-caption"]),
    ("Inline meaning and annotation", [
        ("a", "A link with a destination."),
        ("span", "A neutral inline container."),
        ("em", "Stress that changes the sentence's emphasis."),
        ("strong", "Importance or urgency in context."),
        ("b", "A keyword brought to attention without extra importance."),
        ("i", "An alternate voice or term, not a generic italic command."),
        ("u", "An unarticulated annotation, such as a marked spelling issue."),
        ("small", "A side comment or fine print."),
        ("s", "Text no longer accurate or relevant."),
        ("mark", "Text relevant to a current reference or search."),
        ("abbr", "An abbreviation, optionally with its expansion."),
        ("dfn", "The term being defined."),
        ("cite", "The title of a cited work."),
        ("q", "A quotation kept inline with surrounding prose."),
        ("code", "Computer code or an identifier from code."),
        ("kbd", "Input the user provides to a system."),
        ("samp", "Sample output from a program or device."),
        ("var", "A variable or replaceable value."),
        ("data", "Visible content paired with a machine value."),
        ("time", "A date or time with a machine-readable value."),
        ("sub", "A subscript with actual textual meaning."),
        ("sup", "A superscript with actual textual meaning."),
        ("br", "A meaningful line break within a passage."),
        ("wbr", "An optional break point in a long token."),
        ("bdi", "Isolation for text whose direction is unknown."),
        ("bdo", "An explicit override of text direction."),
        ("ruby", "A base text with short pronunciation or other annotation."),
        ("rt", "The annotation inside ruby."),
        ("rp", "Fallback punctuation around ruby annotation."),
        ("ins", "Content inserted into a revision."),
        ("del", "Content removed in a revision."),
    ], ["html/inline-text-meaning", "html/mark-relevant-text", "html/kbd-samp-var", "html/language-and-direction"]),
    ("Tables and data relationships", [
        ("table", "A grid whose rows and columns describe related data."),
        ("caption", "The table's name and context."),
        ("colgroup", "A group of table columns."),
        ("col", "One column within a column group."),
        ("thead", "Rows that head a table."),
        ("tbody", "The table's body rows."),
        ("tfoot", "Rows that summarize or close a table."),
        ("tr", "A row of cells."),
        ("th", "A header cell associated with data cells."),
        ("td", "A data cell."),
    ], ["html/data-tables", "html/complex-table-headers", "html/table-caption-and-summary"]),
    ("Forms and values", [
        ("form", "The owner of a submission contract."),
        ("label", "A visible name associated with one form control."),
        ("input", "A type-dependent input control."),
        ("button", "A native action or submit control; set its type explicitly."),
        ("select", "A choice control backed by options."),
        ("option", "One selectable choice."),
        ("optgroup", "A named group of related choices."),
        ("datalist", "Suggestions that do not close free text entry."),
        ("textarea", "Multiline text input."),
        ("fieldset", "A related group of controls."),
        ("legend", "The fieldset's group name."),
        ("output", "A calculated result associated with inputs."),
        ("progress", "Completion of an ongoing task."),
        ("meter", "A measured value against a known range."),
    ], ["html/forms-get-post", "html/form-labels", "html/number-step-boundaries"]),
    ("Images, media, and embedded documents", [
        ("img", "An image with an alt decision."),
        ("picture", "Alternative image sources with one fallback img."),
        ("source", "A media or picture source candidate."),
        ("audio", "An audio resource, usually with native controls."),
        ("video", "A moving-image resource, usually with native controls."),
        ("track", "Timed text such as captions or subtitles."),
        ("iframe", "A nested document with its own trust boundary."),
        ("embed", "An external embedded resource; evaluate fallback needs."),
        ("object", "An embedded resource that can include fallback content."),
        ("canvas", "A scriptable bitmap that needs equivalent information."),
        ("map", "A group of clickable regions on an image."),
        ("area", "One region inside an image map."),
    ], ["html/image-alt", "html/video-captions", "html/iframe-sandbox"]),
    ("Browser-managed UI and components", [
        ("details", "A disclosure the browser can open and close."),
        ("summary", "The visible control naming a details disclosure."),
        ("dialog", "A dialog box, with modal behavior only when opened modally."),
        ("script", "Executable script or a typed non-executable data block."),
        ("noscript", "Fallback content in the script-disabled case."),
        ("template", "Inert markup held for later use or a declarative shadow root."),
        ("slot", "A placement point in a shadow tree."),
    ], ["html/dialog-and-details", "html/template-inert-markup", "html/custom-elements"]),
]
seen = [name for _, items, _ in groups for name, _ in items]
assert len(seen) == len(set(seen)), "duplicate element in reference"
reference["body"] = (
    "<p>HTML elements describe document roles, text meaning, controls, and embedded resources. This working index groups commonly authored elements by the problem they solve. An element's browser behavior and permitted children still need to be checked in its focused lesson before use.</p>"
    + "".join(
        "<h2>" + heading + "</h2><ul>"
        + "".join("<li><strong>" + html.escape(name) + "</strong>: " + description + "</li>" for name, description in items)
        + "</ul><p>Related lessons:</p><ul>" + linked(paths) + "</ul>"
        for heading, items, paths in groups
    )
    + "<h2>One complete document</h2>"
    + '<pre><code class="language-html">'
    + html.escape('''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Case C-47 | Intake</title></head>
<body>
  <header><nav aria-label="Primary"><a href="/cases">Cases</a></nav></header>
  <main>
    <article>
      <h1>Case C-47</h1>
      <p><strong>Held:</strong> the upper seal split at intake.</p>
      <section aria-labelledby="evidence-heading">
        <h2 id="evidence-heading">Evidence</h2>
        <p>Recorded at <time datetime="2026-10-01T08:14">08:14</time>.</p>
      </section>
    </article>
  </main>
</body>
</html>''', quote=False)
    + "</code></pre>"
    + "<h2>Cost and scope</h2><p>Native elements add almost no runtime weight. The expensive errors come from using a visual substitute for a browser contract, such as a generic container that needs custom keyboard handling or a grid that hides table relationships. This index is a decision aid, not a license to place every listed element in one document. SVG and MathML have their own vocabularies; custom elements require an implementation and a readable fallback. Verify newer component features in the browsers you support.</p>"
    + "<h3>Common Mistakes</h3><ul><li>Do not select an element solely for its default appearance.</li><li>Do not give a control a label without wiring the action or form endpoint.</li><li>Do not assume a category list replaces validation of a specific content model.</li></ul>"
)
reference["updated_at"] = stamp
reference["data"]["related"] = [
    {"path": path, "title": by_path[path]["title"]}
    for path in ["html/document-skeleton", "html/landmarks", "html/inline-text-meaning", "html/forms-get-post", "html/data-tables", "html/image-alt"]
]


def organize(hub_path, groups):
    hub = by_path[hub_path]
    current = [path for module in hub["data"]["modules"] for path in module["lessons"]]
    arranged = [path for _, _, paths in groups for path in paths]
    assert len(arranged) == len(set(arranged)), hub_path
    assert set(arranged) == set(current) | {path for path in arranged if path not in current and by_path[path]["data"]["section_path"] == hub_path}, hub_path
    hub["data"]["modules"] = [
        {"title": title, "summary": summary, "lessons": paths} for title, summary, paths in groups
    ]
    hub["body"] = (
        "<p>" + hub["summary"] + "</p>"
        + "".join("<h2>" + title + "</h2><p>" + summary + "</p><ul>" + linked(paths) + "</ul>" for title, summary, paths in groups)
        + '<p><a href="/html/html-tutorial">Return to the HTML tutorial</a>.</p>'
        + "<h3>Common Mistakes</h3><p>A lesson's illustrative route, component, or asset is not a deployed application feature.</p>"
    )
    hub["updated_at"] = stamp


organize("html/html-tutorial/semantics", [
    ("Page regions", "Give each major area a clear purpose and reading position.", ["html/landmarks", "html/sections-and-articles", "html/figure-and-caption", "html/search-element", "html/address-contact-info"]),
    ("Text, language, and revision", "Represent quotations, machine values, changes, and mixed-language text honestly.", ["html/time-and-machine-values", "html/quotes-and-citations", "html/ruby-annotations", "html/bidi-isolation", "html/data-element-values", "html/ins-and-del", "html/word-break-opportunities", "html/translate-boundaries", "html/mark-relevant-text", "html/br-and-hr-boundaries", "html/kbd-samp-var"]),
    ("Tables and diagrams", "Make data associations explicit and keep vector meaning available.", ["html/data-tables", "html/complex-table-headers", "html/table-spans", "html/table-column-groups", "html/inline-svg"]),
])

organize("html/html-tutorial/media", [
    ("Images and alternatives", "Choose useful image text, responsive sources, and intentional load timing.", ["html/image-alt", "html/responsive-images", "html/picture-art-direction", "html/image-loading-priority", "html/image-decoding-hint", "html/image-maps"]),
    ("Audio and video", "Keep spoken and visual information available beyond playback.", ["html/video-captions", "html/audio-controls", "html/video-source-fallback", "html/video-poster-preload", "html/video-track-languages", "html/video-descriptive-transcript", "html/audio-transcript"]),
    ("Embedded resources", "Name frames, constrain capabilities, and provide alternate paths.", ["html/iframe-sandbox", "html/iframe-srcdoc-boundary", "html/iframe-permissions", "html/lazy-iframe-loading", "html/object-fallback", "html/mathml-in-html"]),
    ("Script delivery", "Load enhancement code without making content depend on it.", ["html/script-loading"]),
])

organize("html/html-tutorial/accessibility", [
    ("Reading and keyboard order", "Use native controls, landmarks, and focus order before adding ARIA.", ["html/focus-and-native-controls", "html/skip-link", "html/focus-order-tabindex", "html/aria-current-navigation"]),
    ("Visibility and disclosure", "Keep rendered state, interaction state, and accessibility exposure aligned.", ["html/hidden-and-inert", "html/dialog-and-details", "html/exclusive-details-groups"]),
    ("Language and feedback", "Expose changed information and meaningful names to the right audience.", ["html/language-and-direction", "html/live-status", "html/noscript-fallback", "html/linked-image-alt", "html/table-caption-and-summary"]),
    ("Form repair", "Make field instructions, requirements, and validation errors actionable.", ["html/form-help-and-errors", "html/aria-invalid-errors", "html/autofocus-dialog"]),
    ("Template boundary", "Keep staged markup from becoming a hidden interaction trap.", ["html/template-inert-markup"]),
])

organize("html/html-tutorial/advanced", [
    ("Browser-managed panels", "Pick a nonmodal panel or dialog for the actual task.", ["html/native-popover", "html/dialog-form-method", "html/hidden-until-found"]),
    ("Component boundaries", "Preserve fallback content as custom elements and shadow trees upgrade.", ["html/custom-elements", "html/declarative-shadow-dom", "html/slots-and-fallback", "html/form-associated-custom-elements"]),
    ("Scripts and embedded data", "Keep module names, script data, and load order under control.", ["html/script-modules", "html/script-import-maps", "html/scripting-escape-and-json"]),
    ("Graphics", "Retain the underlying information when drawing to a bitmap.", ["html/canvas-fallback"]),
])

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Expanded the element reference, added three semantic lessons, and organized four hubs.")

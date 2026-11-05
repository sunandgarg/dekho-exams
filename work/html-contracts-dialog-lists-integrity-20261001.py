"""Fill five distinct HTML gaps and place every recent lesson in its right path."""

import base64
import copy
import datetime
import hashlib
import html
import json
import uuid
from pathlib import Path


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
font_hash = base64.b64encode(hashlib.sha384((root / "public/fonts/fonts.css").read_bytes()).digest()).decode()


def links(paths):
    return "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    )


def move(path, hub_path, module_title):
    hub = by_path[hub_path]
    for module in hub["data"]["modules"]:
        if path in module["lessons"]:
            module["lessons"].remove(path)
    matching = [module for module in hub["data"]["modules"] if module["title"] == module_title]
    assert len(matching) == 1, (path, hub_path, module_title)
    matching[0]["lessons"].append(path)
    hub["updated_at"] = stamp


def add_article(path, title, summary, hub_path, module_title, intro, decision, sample, cost, mistakes, related):
    assert path not in by_path
    assert all(key in by_path for key in related)
    body = (
        "<p>" + intro + "</p><h2>Choose the contract</h2><p>" + decision + "</p>"
        '<pre><code class="language-html">' + html.escape(sample, quote=False) + "</code></pre>"
        "<h2>Cost and verification</h2><p>" + cost + "</p>"
        "<h3>Common Mistakes</h3><ul>"
        + "".join("<li>" + item + "</li>" for item in mistakes)
        + "</ul><h2>Connected lessons</h2><ul>" + links(related) + "</ul>"
    )
    entry = copy.deepcopy(by_path["html/file-accept-hint"])
    entry.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path, title=title, summary=summary, body=body,
        subject=by_path[hub_path]["subject"], tags=["html", "browser-contract"],
        sort_order=4000 + len(rows), created_at=stamp, updated_at=stamp, published_at=stamp,
    )
    entry["data"] = {
        "subject_root": "html/html-tutorial", "section_path": hub_path,
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
    move(path, hub_path, module_title)


move("html/video-playsinline", "html/html-tutorial/media", "Audio and video")
move("html/modulepreload", "html/html-tutorial/advanced", "Scripts and embedded data")
move("html/manual-popover", "html/html-tutorial/advanced", "Browser-managed panels")

add_article(
    "html/ordered-list-numbering",
    "HTML ordered-list numbering: keep source order and displayed rank aligned",
    "Use start and reversed when the ordinal value belongs to the content.",
    "html/html-tutorial", "Readable text and code",
    "An ordered list says that item order changes meaning. Its start value and reversed state affect the displayed ordinals; they do not reorder the list items in the document.",
    "A case report excerpt begins at procedure step four because the first three steps are in an earlier section. The visible number must match the written instruction, so start is meaningful here. A separate countdown is explicitly descending and uses reversed. Keep the source in the same reading order as the screen. If a design merely wants a different marker shape, use styling instead of inventing a new sequence. The browser counts direct list items, including ones whose content wraps or includes nested prose; manually typing numbers into the text creates two competing numbering systems. For a procedure split across pages, confirm that the sequence and links to earlier steps remain understandable without CSS.",
    '''<section aria-labelledby="handoff-steps">
  <h2 id="handoff-steps">Parcel handoff, continued</h2>
  <ol start="4">
    <li>Match the seal code to the intake record.</li>
    <li>Place the parcel in bay C-47.</li>
    <li>Record the receiving officer.</li>
  </ol>
  <h2>Final checks before release</h2>
  <ol reversed>
    <li>Confirm the receiving signature.</li>
    <li>Verify the bay assignment.</li>
    <li>Check the seal photograph.</li>
  </ol>
</section>''',
    "The markup has negligible transfer cost and requires no script. The first list renders 4, 5, 6; the three-item reversed list renders 3, 2, 1. If items are inserted or removed, reversed numbering without an explicit start adjusts to the number of list items. Test the labels with styles disabled and with a screen reader, particularly if CSS replaces markers. A skipped rank can be deliberate, but it should be explained in content rather than hidden in a value attribute.",
    ["Do not use CSS order to reverse the visual list while leaving reading order unchanged.", "Do not type a second number inside each list item.", "Do not use an ordered list for unrelated cards merely because the design numbers them."],
    ["html/lists-and-definitions", "html/headings-and-paragraphs", "html/sections-and-articles"],
)

add_article(
    "html/dialog-command-buttons",
    "HTML dialog commands: open and request close with named buttons",
    "Use command and commandfor for declarative dialog controls where supported.",
    "html/html-tutorial/advanced", "Browser-managed panels",
    "A button can target a dialog by ID and ask the browser to show it modally or request that it close. This is an interface action, not a form submission or a saved business decision.",
    "A reviewer opens a seal-policy note while completing an intake form. The opening button is explicitly type=button so it cannot submit an enclosing form by accident. Inside the dialog, another button requests closure and gives users a visible way back. A close request may pass through cancel handling, unlike an unconditional close; code that needs to guard unsaved work should test that behavior in the actual browser. The policy text is read-only, so a dialog may be excessive if it could simply remain on the page. Use it when the context calls for a modal interruption. Before depending on these declarative commands, verify support in the browsers your audience uses and provide a tested alternate control when necessary.",
    '''<button type="button" commandfor="seal-policy" command="show-modal">
  Read seal policy
</button>
<dialog id="seal-policy" aria-labelledby="seal-policy-title">
  <h2 id="seal-policy-title">Seal policy for bay C-47</h2>
  <p>Hold parcels with a broken upper seal until a second reviewer signs.</p>
  <button type="button" commandfor="seal-policy" command="request-close">
    Return to intake
  </button>
</dialog>''',
    "The native dialog handles top-layer placement and modal focus behavior without a custom overlay library. The markup still needs keyboard, focus-return, and small-screen tests, and the policy must remain available if the feature is unsupported. No network request is made by either button. The ID must resolve within the same tree, and the targeted element must actually be a dialog. Do not add a script merely to recreate built-in behavior when the supported browser set already provides it.",
    ["Do not omit type=button inside or near a form.", "Do not read a close request as proof that an incident was approved.", "Do not ship the command pair without testing the target browser and a visible escape path."],
    ["html/dialog-and-details", "html/dialog-form-method", "html/focus-and-native-controls"],
)

add_article(
    "html/dialog-closedby",
    "HTML dialog closedby: choose whether outside clicks dismiss a panel",
    "Use closedby=any only when losing the panel carries no unsaved work.",
    "html/html-tutorial/advanced", "Browser-managed panels",
    "The closedby attribute sets which user dismissal actions close a dialog. In particular, any permits both close requests and outside clicks; closerequest allows close requests without outside-click dismissal; none disables automatic user dismissal.",
    "A short reference note can safely disappear when the reviewer clicks outside it. That makes any a sensible choice, provided the note has an obvious close button as well. The same setting would be risky on an edit form containing unsaved evidence, because an incidental click could discard work. The attribute does not turn a dialog modal; how the dialog is opened still controls modality. It also does not change a server record. The example opens the note as a modal with a named button. Test keyboard close, pointer dismissal, and focus return in each target browser, since support for this newer attribute can differ from support for dialog itself.",
    '''<button type="button" commandfor="bay-note" command="show-modal">
  Read bay note
</button>
<dialog id="bay-note" closedby="any" aria-labelledby="bay-note-title">
  <h2 id="bay-note-title">Bay C-47 note</h2>
  <p>Place sealed parcels on the upper shelf only.</p>
  <button type="button" commandfor="bay-note" command="request-close">
    Close note
  </button>
</dialog>''',
    "This costs no application script when the browser supports both dialog commands and closedby. A fallback for unsupported browsers must be tested rather than assumed. If the panel later gains editable fields, revisit the dismissal policy and provide a save or discard path before keeping any. Do not manually remove the open attribute to imitate closing: that bypasses normal close behavior and can leave modal state inconsistent. The visible close control remains important even when light dismissal works.",
    ["Do not put unsaved form data in a dialog that light-dismisses without a recovery path.", "Do not assume closedby alone opens the dialog.", "Do not remove open directly as a substitute for a close operation."],
    ["html/dialog-command-buttons", "html/dialog-and-details", "html/manual-popover"],
)

add_article(
    "html/iframe-referrerpolicy",
    "HTML iframe referrerpolicy: limit parent-page details sent to an embed",
    "Set an iframe referrer policy when its initial request should not reveal the parent URL.",
    "html/html-tutorial/media", "Embedded resources",
    "An iframe has its own navigation request. Its referrerpolicy attribute controls referrer information for that request; it does not make the framed document trustworthy or anonymous.",
    "An intake record embeds a help panel that is maintained by a separate route. The parent URL may contain a case identifier, so the frame request should not carry it as a referrer. A no-referrer policy makes that intent explicit. The child can still learn anything placed in its own requested URL, messages sent by the parent, or data available through other permitted interfaces. Keep identifiers out of the frame source when they are unnecessary, use a clear title, and assess the origin and sandbox policy separately. A same-origin frame may have broad access to its parent unless another boundary changes that relationship. Referrer policy addresses one channel only; it does not grant isolation.",
    '''<section aria-labelledby="intake-help-heading">
  <h2 id="intake-help-heading">Intake help</h2>
  <iframe src="/help/intake-rules" title="Parcel intake rules"
          width="560" height="420" loading="lazy"
          referrerpolicy="no-referrer"></iframe>
  <p>The intake rules are also available as ordinary page text.</p>
</section>''',
    "The frame creates another document and potentially its own script, style, and image requests. Lazy loading can defer that cost when help starts below the fold, but it does not remove it. Test the actual request headers, frame title, keyboard entry and exit, and failure display. The local help route in the sample must exist before deployment. For an untrusted external origin, evaluate sandbox and permissions separately; referrerpolicy does not stop the embedded page from running code or requesting features allowed to it.",
    ["Do not place a case token in src and expect no-referrer to hide it.", "Do not confuse referrer policy with iframe sandboxing.", "Do not assume the content between iframe tags is reliable fallback in modern browsers."],
    ["html/iframe-sandbox", "html/iframe-permissions", "html/anchor-referrer-policy"],
)

add_article(
    "html/subresource-integrity",
    "HTML subresource integrity: bind a stylesheet to the bytes you reviewed",
    "Use integrity for a fixed external stylesheet or script and update the digest with the asset.",
    "html/html-tutorial", "Links and resource boundaries",
    "An integrity attribute tells the browser which digest a fetched stylesheet or script must match before it is applied or executed. A mismatch is a load failure, not a soft warning.",
    "The example pins a local stylesheet to the exact version included in this site's public assets. The digest is computed from its bytes, not typed as an illustrative placeholder. If the stylesheet changes, regenerate the digest in the same build step that changes the asset; otherwise the browser will reject the new file and the page may lose its intended presentation. Keep meaningful text and controls usable without that stylesheet. Integrity is especially useful when the HTML and resource come from different trust paths, but a same-origin example demonstrates the mechanism without relying on another service. It cannot protect against an attacker who can replace both the HTML and its digest.",
    '<head>\n  <title>Receipt R-47</title>\n  <link rel="stylesheet" href="/fonts/fonts.css"\n        integrity="sha384-' + font_hash + '">\n</head>\n<body>\n  <main>\n    <h1>Receipt R-47</h1>\n    <p>Review the receipt without depending on a custom font.</p>\n  </main>\n</body>',
    "The hash check adds small verification work but no separate network request. It does not reduce CSS bytes, replace a content security policy, or guarantee that the asset itself is safe. For a cross-origin resource, the request must use CORS and the server must permit it; the local file shown here is same-origin. The content checker recomputes this sample's SHA-384 digest from the asset, so a future edit that leaves the lesson stale fails validation. Verify the final deployed bytes too, because a CDN transformation after hashing would cause a mismatch.",
    ["Do not copy a digest from a different asset or release.", "Do not treat integrity as protection when the same attacker can rewrite the HTML.", "Do not silently remove the hash when a mismatch reveals a build or delivery error."],
    ["html/resource-hints", "html/print-stylesheet-media", "html/script-loading"],
)


for hub_path in ["html/html-tutorial", "html/html-tutorial/forms", "html/html-tutorial/media", "html/html-tutorial/advanced"]:
    hub = by_path[hub_path]
    lead = {
        "html/html-tutorial": "Document setup, text, links, and resource boundaries.",
        "html/html-tutorial/forms": "Build forms from the values and server behavior they actually require.",
        "html/html-tutorial/media": "Images, timed media, frames, and their resource costs.",
        "html/html-tutorial/advanced": "Browser-managed panels, components, scripts, and graphics.",
    }[hub_path]
    hub["body"] = (
        "<p>" + lead + "</p>"
        + "".join("<h2>" + module["title"] + "</h2><p>" + module["summary"] + "</p><ul>" + links(module["lessons"]) + "</ul>" for module in hub["data"]["modules"])
        + "<h3>Common Mistakes</h3><p>Each lesson explains a browser contract. An illustrative asset or endpoint is not a deployed service until its owner supplies and verifies it.</p>"
    )
    hub["updated_at"] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added five articles, repaired recent module placement, and rebuilt four hubs")

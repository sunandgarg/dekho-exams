"""Add distinct HTML browser contracts and repair the comparison/quiz paths."""

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


def add_article(path, title, summary, hub_path, intro, decision, sample, cost, mistakes, related):
    assert path not in by_path
    assert all(key in by_path for key in related)
    body = (
        "<p>" + intro + "</p><h2>Decide from the browser contract</h2><p>" + decision + "</p>"
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
    hub = by_path[hub_path]
    hub["data"]["modules"][-1]["lessons"].append(path)
    hub["body"] += '<p><a href="/' + path + '">' + html.escape(title) + "</a>.</p>"
    hub["updated_at"] = stamp


add_article(
    "html/file-capture-hint",
    "HTML file capture: suggest a camera without treating it as permission",
    "Use capture on a file input as a device-facing hint, then validate the selected image.",
    "html/html-tutorial/forms",
    "The capture attribute can express a preferred camera-facing mode on a file upload control. It cannot guarantee that a camera exists, that a particular picker opens, or that the returned bytes are safe.",
    "A depot worker photographs a damaged seal at intake. The form asks for an image and suggests the rear camera, while its visible instruction still works if the device offers an ordinary file picker. The selected file remains user-controlled input. The upload handler must authenticate the worker, limit bytes, inspect the decoded image, remove metadata if policy requires it, and associate the result with the correct case. Explain retention before submission; a photograph may contain location or personal details unrelated to the damage. Capture is a preference, not a hidden permission grant or a replacement for a normal upload path.",
    '''<form action="/intake/I-47/seal-photo" method="post" enctype="multipart/form-data">
  <label for="seal-photo">Damaged seal photo</label>
  <p id="seal-photo-help">Take a photo or choose an existing image. Maximum 6 MB.</p>
  <input id="seal-photo" name="sealPhoto" type="file"
         accept="image/*" capture="environment"
         aria-describedby="seal-photo-help" required>
  <button type="submit">Attach photo</button>
</form>''',
    "The attribute adds no script or network request. Image decoding, malware screening, storage, and retention create the operational cost; the form route shown here requires a real authenticated handler before use. Test rear- and front-camera devices, desktop browsers, denied camera access, picker fallback, and files with misleading extensions. Do not infer image dimensions, MIME validity, or safety from the picker hint. If a photo is optional for a particular case, remove required and explain the alternate evidence path in visible text.",
    ["Do not describe capture as a promise to open the rear camera on every browser.", "Do not trust accept or the filename as server validation.", "Do not collect a photo without a clear retention and access rule."],
    ["html/file-accept-hint", "html/file-upload-form", "html/form-help-and-errors"],
)

add_article(
    "html/video-playsinline",
    "HTML video playsinline: request inline playback without forcing autoplay",
    "Use playsinline to ask for playback in the page while retaining controls and captions.",
    "html/html-tutorial/media",
    "The playsinline boolean attribute encourages a browser to keep video inside its element's playback area. It does not start playback, prevent fullscreen controls, or guarantee the same presentation on every device.",
    "An incident report embeds a short inspection clip beside the written finding. The reviewer should choose when to play it, so controls stay visible and autoplay is absent. Inline playback can preserve nearby context on a narrow screen, yet a reader may still choose fullscreen. A caption track carries speech and meaningful audio; a separate transcript or written finding carries information for people who cannot use the clip. The browser's treatment of playsinline depends on platform behavior, and leaving it out does not itself require fullscreen playback. Test the actual recording on the target mobile browsers rather than promising a fixed layout.",
    '''<section aria-labelledby="inspection-heading">
  <h2 id="inspection-heading">Inspection I-47 clip</h2>
  <video controls playsinline preload="none" width="640" height="360">
    <source src="/media/I-47-inspection.mp4" type="video/mp4">
    <track kind="captions" src="/media/I-47-captions.vtt"
           srclang="en" label="English" default>
    <p>Read the inspection finding below if video playback is unavailable.</p>
  </video>
  <p>The seal split at its upper corner before dispatch.</p>
</section>''',
    "Playsinline itself has no transfer cost. The clip, caption file, poster if present, and transcript do; preload=none is only a fetch hint, so inspect network behavior on the real page. The media paths in the markup must be supplied before publication. Keep a visible finding even if the video cannot play, check caption timing, and verify keyboard access to native controls. An inline layout may need responsive CSS, but CSS should not remove the user's fullscreen option.",
    ["Do not pair playsinline with autoplay merely to make the attribute appear to work.", "Do not treat fallback text inside video as a substitute for captions.", "Do not assume every mobile browser will render identically."],
    ["html/video-poster-preload", "html/video-captions", "html/video-descriptive-transcript"],
)

add_article(
    "html/modulepreload",
    "HTML modulepreload: fetch a known module before its import is discovered",
    "Use modulepreload only for a measured module dependency needed on the current route.",
    "html/html-tutorial/advanced",
    "A modulepreload link fetches a JavaScript module with module-script rules and places it in the document's module map. Ordinary preload is not an interchangeable spelling for that behavior.",
    "A receipt detail route loads a module that imports a formatter used before the first interaction. When a network trace shows that dependency starts late, preloading the same deployed module path can shorten the wait. The script tag still executes the entry module; the link alone does not run code. Browsers may fetch declared dependencies as an optimization, but do not rely on a particular dependency traversal or event timing. Keep the preload list short and generated from the build output, because a renamed chunk silently turns the hint into wasted transfer. If the module is only needed after a rare click, an early fetch may compete with CSS, text, or the receipt image.",
    '''<head>
  <title>Receipt R-47</title>
  <link rel="modulepreload" href="/assets/receipt-format.mjs">
  <script type="module" src="/assets/receipt-view.mjs"></script>
</head>
<body>
  <main>
    <h1>Receipt R-47</h1>
    <p id="receipt-total">Total will appear after the module loads.</p>
  </main>
</body>''',
    "Both module paths must exist in the deployed build, and the entry module must import the preloaded dependency at the same resolved URL for reuse. A preload moves bytes earlier; it neither reduces the module's size nor executes it. Compare a cold-load network trace and the page's meaningful render before and after adding the hint, including a slow connection. Remove it when the dependency is no longer critical. Keep the server's module MIME type, cache policy, and cross-origin rules aligned with the actual script request.",
    ["Do not use rel=preload with as=script and assume it populates the module map.", "Do not preload every chunk produced by a bundler.", "Do not leave a stale hashed filename in a hand-written template."],
    ["html/resource-hints", "html/script-modules", "html/image-loading-priority"],
)

add_article(
    "html/manual-popover",
    "HTML manual popover: keep a nonmodal panel open until a deliberate close",
    "Use popover=manual when light dismissal would interrupt a nonmodal task.",
    "html/html-tutorial/advanced",
    "A manual popover does not light-dismiss when the user clicks outside it and does not close merely because another popover opens. It remains nonmodal, so the rest of the page is still available.",
    "A reviewer compares a hold-code explanation with several fields in the same record. An auto popover would disappear on an outside click, which interrupts the comparison. Manual mode keeps the note visible while the reviewer works elsewhere, and an explicit button inside the panel closes it. The trigger and close button identify the same popover by ID. This is a deliberate interface choice: if a task must block the page, use a modal dialog instead; if brief help should vanish on outside interaction, use auto. A persistent nonmodal panel needs a close path that remains discoverable to keyboard and touch users.",
    '''<button type="button" popovertarget="hold-note" popovertargetaction="show">
  Show hold-code note
</button>
<section id="hold-note" popover="manual" aria-labelledby="hold-note-heading">
  <h2 id="hold-note-heading">Hold code H-47</h2>
  <p>Keep the parcel out of export until the seal review is recorded.</p>
  <button type="button" popovertarget="hold-note" popovertargetaction="hide">
    Close note
  </button>
</section>''',
    "Native show and hide avoid a custom click-away listener, though the panel still needs positioning and overlap checks on small screens. The markup does not store the reviewer's decision or enforce a hold on the server; those are separate application contracts. Test focus movement, Escape expectations, outside clicks, and access to the close button on supported browsers. If the panel must persist across navigation, that persistence needs explicit application state and should be communicated to users rather than inferred from the attribute.",
    ["Do not expect outside clicks to close a manual popover.", "Do not omit an obvious close control.", "Do not use a nonmodal popover for a blocking confirmation."],
    ["html/native-popover", "html/dialog-vs-popover", "html/focus-and-native-controls"],
)


def rebuild_hub(path, intro, groups, warning):
    hub = by_path[path]
    hub["data"]["modules"] = [
        {"title": title, "summary": summary, "lessons": lessons}
        for title, summary, lessons in groups
    ]
    hub["body"] = (
        "<p>" + intro + "</p>"
        + "".join("<h2>" + title + "</h2><p>" + summary + "</p><ul>" + links(lessons) + "</ul>" for title, summary, lessons in groups)
        + "<h3>Common Mistakes</h3><p>" + warning + "</p>"
    )
    hub["updated_at"] = stamp


rebuild_hub(
    "html/html-tutorial/comparison",
    "Use these comparisons when two elements or attributes seem to solve the same task but leave different browser behavior behind.",
    [
        ("Actions and destinations", "Choose native actions for operations and links for navigation.", ["html/button-tag-vs-input-typebutton-attribute", "html/link-vs-button"]),
        ("Form state and labels", "Separate browser validation, submission state, and visible field identity.", ["html/required-vs-aria-required", "html/readonly-vs-disabled", "html/placeholder-vs-label"]),
        ("Visibility and panels", "Decide whether content is hidden, dismissible, or blocking.", ["html/hidden-vs-aria-hidden", "html/dialog-vs-popover"]),
        ("Data relationships", "Use table structure for actual row and column relationships.", ["html/table-vs-layout"]),
    ],
    "A similar appearance does not make two controls interchangeable. Test keyboard behavior and submitted values, not just the rendered layout.",
)

rebuild_hub(
    "html/quizzes",
    "Each twelve-question bank checks a browser contract against the application work needed to make it useful.",
    [
        ("Document and markup decisions", "Start with structure, meanings, and the shape of a complete page.", ["quizzes/html-document-structure", "quizzes/html-markup-decisions"]),
        ("Forms and applied production", "Check submission, accessibility, and server boundaries.", ["quizzes/html-forms-and-accessibility", "quizzes/html-production-review", "quizzes/html-browser-contracts"]),
        ("Advanced contracts", "Review components, media, metadata, and less common browser features.", ["quizzes/html-advanced-contracts", "quizzes/html-specialized-contracts"]),
    ],
    "A correct quiz answer does not prove that an illustrative route, asset, or server handler exists in the running site.",
)

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added four articles and rebuilt two hubs")

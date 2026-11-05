"""Add an advanced HTML section with bounded, linked technical lessons."""

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
drafts = []


def add(slug, section, title, definition, case, sample, boundary, cost, mistakes, links):
    drafts.append((slug, section, title, definition, case, sample, boundary, cost, mistakes, links))


add("parser-and-void-elements", "core", "HTML parsing: void elements and repaired markup",
    "The HTML parser builds a document tree from tokens and may repair malformed nesting instead of rejecting the page.",
    "A receipt page should never depend on that repair. The image, line break, and input are void elements and have no closing tags or child content. Headings and paragraphs have clear starts and ends, so the intended DOM is easy to inspect. A browser may close a paragraph when a section begins, but another tool reading the source may expose the mistake differently.",
    '''<main>
  <h1>Receipt R-47</h1>
  <p>Review the receipt before export.<br>Keep the record ID visible.</p>
  <img src="/media/receipt-mark.svg" alt="" width="36" height="36">
  <label for="review-code">Review code</label>
  <input id="review-code" name="review_code" type="text">
</main>''',
    "The image path needs an owned asset. An empty alt is justified here only if this mark adds no information beyond the nearby heading. Parsing rules do not make an invalid document a sound content model; inspect the DOM that the browser actually constructed.",
    "Parser repair may appear cheap, but debugging a DOM that differs from source costs time and can change CSS or scripting behavior. Keep tags explicit in authored examples and validate generated HTML.",
    ["Do not add children to img or input.", "Do not depend on a browser silently closing misplaced paragraphs.", "Do not confuse source text with the final DOM tree."],
    ["html/document-skeleton", "html/image-alt", "html/character-references"])

add("base-element-paths", "core", "HTML base: change how every relative URL resolves",
    "A base element in head sets the base URL used to resolve relative URLs in that document.",
    "A receipt archive may serve pages under one shared route prefix. The base makes a bare record path resolve beneath that prefix, but the same rule also affects relative images, stylesheets, form actions, and fragment links. That reach makes base a document-wide decision, not a shortcut for one link. Root-relative paths avoid this dependency when several route families share a page.",
    '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <base href="/receipts/">
  <title>Receipt archive</title>
</head>
<body>
  <main><h1>Archive</h1><a href="R-47">Open R-47</a></main>
</body>
</html>''',
    "The link resolves to the receipt route only if the server actually serves it. A fragment-only link may also resolve against the base instead of the current page, so test it before adding a skip link or table of contents.",
    "One base element adds no runtime code, yet it can redirect many requests after a small edit. Teams with mixed assets and routes often spend less maintenance effort on explicit root-relative paths.",
    ["Do not assume a fragment link stays on the current document after adding base.", "Do not place base after links that must resolve consistently.", "Do not use it to hide missing routes."],
    ["html/anchors-and-paths", "html/skip-link", "html/document-skeleton"])

add("resource-hints", "core", "HTML resource hints: preload only a known critical asset",
    "Link relations can load a stylesheet or hint that a specific resource should be fetched early.",
    "A receipt detail page needs its local stylesheet. Its mark may be the main image above the fold, so a matching preload can help if measurement shows that the image request starts late. A preload is not a general performance badge: if the image is absent, has a different candidate URL, or is hidden on the target route, the early transfer can waste bandwidth.",
    '''<head>
  <link rel="stylesheet" href="/assets/receipt-page.css">
  <link rel="preload" as="image" href="/media/receipt-mark-47.webp">
</head>
<body>
  <main>
    <h1>Receipt R-47</h1>
    <img src="/media/receipt-mark-47.webp" alt="Receipt R-47 mark" width="320" height="180">
  </main>
</body>''',
    "Both files must exist at the specified local paths. The image preload and the rendered image use the same URL; responsive image selection, credentials, and content type can make a more complex case require more careful matching.",
    "Preload moves a request earlier; it does not shrink bytes. Compare a real page load before and after, especially on slow connections where an unnecessary preload competes with CSS or text.",
    ["Do not preload every image on a long page.", "Do not point a hint at an asset the route never uses.", "Keep stylesheet and image paths aligned with deployed assets."],
    ["html/image-loading-priority", "html/responsive-images", "html/metadata-title"])

add("new-tab-links", "core", "HTML links in a new tab: preserve context without hiding the action",
    "An anchor target can request a new browsing context, but the destination and user expectation still govern whether that choice is useful.",
    "A reviewer may open a printable receipt while keeping an unfinished review form available. The link names that behavior plainly. Modern browsers generally isolate a blank-target page from its opener; an explicit noopener relationship makes the intent visible in the source. A separate tab can still disorient users, so ordinary internal reading links should stay in the current context by default.",
    '''<p>Keep this review form open while checking the source record.</p>
<a href="/receipts/R-47/print" target="_blank" rel="noopener">
  Open printable receipt R-47 in a new tab
</a>''',
    "The print route must be implemented and authorization checked by the server. The new tab is not a security boundary for private record access, and it is not a way to preserve unsaved form data reliably.",
    "Opening a tab adds a document load and can duplicate application memory. Use it only when the task genuinely benefits from simultaneous contexts, then test keyboard and mobile behavior.",
    ["Do not open every link in a new tab.", "Do not hide the new-tab behavior from link text.", "Do not treat target or rel as authorization."],
    ["html/anchors-and-paths", "html/link-vs-button", "html/forms-get-post"])

add("download-links", "core", "HTML download links: distinguish a file transfer from page navigation",
    "The download attribute on an anchor suggests saving a linked resource instead of opening it as a document.",
    "A reviewer exports a CSV for a single authorized receipt. The visible text states the format and record ID, while the filename gives a useful default when the browser honors it. The application must serve the file and set appropriate response headers; markup cannot decide the server's content type, prevent redirects, or grant permission to a private export.",
    '''<p>Export only after the review is complete.</p>
<a href="/downloads/receipts/R-47.csv" download="receipt-R-47.csv">
  Download receipt R-47 as CSV
</a>''',
    "The download hint is most predictable for same-origin resources. Browser behavior and server headers can influence the result; test a real response rather than assuming the attribute guarantees a saved file.",
    "The markup is tiny. The transfer cost is the file itself, and a generated export may consume CPU and storage. Rate limits and authorization belong on the download endpoint.",
    ["Do not assume download creates the file.", "Do not expose a private export through an unchecked static route.", "Name the format and record in the visible link text."],
    ["html/anchors-and-paths", "html/file-upload-form", "html/receipt-index-project"])

add("complex-table-headers", "semantics", "HTML complex tables: connect each value to all applicable headers",
    "A complex table can use unique header IDs and a headers list on data cells when simple row and column scope cannot express the relationships.",
    "A finance summary crosses quarter and measure. One number belongs to the quarter, the measure, and a row label. Explicit IDs allow the cell to name all three. Before choosing this structure, ask whether two simpler tables would make the data easier to maintain and scan; markup that merely satisfies a parser may still force readers through an awkward grid.",
    '''<table>
  <caption>Receipt review totals</caption>
  <thead>
    <tr><th id="batch" rowspan="2">Batch</th><th id="quarter" colspan="2">Quarter 47</th></tr>
    <tr><th id="approved">Approved</th><th id="held">Held</th></tr>
  </thead>
  <tbody>
    <tr><th id="batch-r47" scope="row">R-47</th>
      <td headers="batch batch-r47 quarter approved">73</td>
      <td headers="batch batch-r47 quarter held">4</td></tr>
  </tbody>
</table>''',
    "Every headers token must match a header cell ID in this table. The numbers here describe one batch only; a production report must calculate them from its actual records and state the unit of measure.",
    "The DOM grows with rows and columns. Explicit associations add authoring work and more ways to introduce broken IDs, so validate them and simplify the table when the data model permits.",
    ["Do not point headers at a td or an ID in another table.", "Do not use merged cells only to make a layout look aligned.", "Provide a caption that names the data set."],
    ["html/data-tables", "html/table-spans", "html/table-vs-layout"])

add("table-spans", "semantics", "HTML table spans: merge cells only when the data relationship requires it",
    "Colspan and rowspan change the table grid; they do not replace header semantics.",
    "A receipt summary reports two measures under one quarter heading. The heading spans both measure columns, while each data row still has its own row header. That is a meaningful merge. If a designer wants a wider cell solely to position text, CSS should handle it outside the data model. Small tables with clear scope are easier to audit than intricate spans.",
    '''<table>
  <caption>Quarter 47 review count</caption>
  <thead>
    <tr><th scope="col" rowspan="2">Batch</th><th scope="colgroup" colspan="2">Quarter 47</th></tr>
    <tr><th scope="col">Approved</th><th scope="col">Held</th></tr>
  </thead>
  <tbody><tr><th scope="row">R-47</th><td>73</td><td>4</td></tr></tbody>
</table>''',
    "The group heading applies to the two measure columns. Test the interpreted header associations with assistive technology for a production report; if the grid becomes harder to explain than the values, split it.",
    "Merged cells add no network requests but make column accounting harder for editors and parsers. The number of rendered cells remains proportional to the dataset, so pagination still matters for large reports.",
    ["Do not allow spans to overlap other cells.", "Do not assume a visual merge names every data cell correctly.", "Keep the row and column counts consistent after edits."],
    ["html/data-tables", "html/complex-table-headers", "html/table-vs-layout"])

add("inline-svg", "semantics", "HTML inline SVG: give a meaningful vector a name",
    "Inline SVG can render vector content in an HTML document and can carry an accessible name when the graphic adds information.",
    "A status icon signals that a receipt is held. The vector is small and crisp at different display densities. Its title and labelled-by relationship identify the graphic, while adjacent text states the same status without depending on color or shape alone. If the symbol were only decoration, it should be hidden from assistive technology instead of receiving a redundant name.",
    '''<p>
  <svg viewBox="0 0 24 24" width="24" height="24" role="img" aria-labelledby="held-icon-title">
    <title id="held-icon-title">Held receipt</title>
    <circle cx="12" cy="12" r="9" fill="currentColor"></circle>
  </svg>
  Receipt R-47 is held for review.
</p>''',
    "This markup provides no decision workflow; it only conveys a status. The color inherits from text styling, but the explicit sentence remains the authoritative visible message when color perception varies.",
    "One small inline shape avoids an asset request. Large repeated SVG trees can add document weight; use a reusable asset or symbol strategy when measurement shows duplication matters.",
    ["Do not communicate status only with fill color.", "Do not give a decorative icon a verbose duplicate name.", "Keep aria-labelledby pointing to an ID inside the graphic."],
    ["html/image-alt", "html/figure-and-caption", "html/live-status"])

add("submit-button-overrides", "forms", "HTML submit overrides: one form, two deliberate destinations",
    "A submit button can override selected form submission attributes for the submission that button initiates.",
    "A receipt editor saves a draft to one endpoint and submits a completed review to another. Both buttons belong to the same form, but only the final action changes the form destination. Each endpoint must validate and authorize its own operation; a client-controlled override is not a privilege boundary. Keep button text explicit because two similarly styled submitters can otherwise hide a material difference.",
    '''<form action="/receipts/R-47/draft" method="post">
  <label for="review-note">Review note</label>
  <textarea id="review-note" name="note" required></textarea>
  <button type="submit">Save draft</button>
  <button type="submit" formaction="/receipts/R-47/finalize">Finalize review</button>
</form>''',
    "Both endpoints receive the successful form controls. A required note still applies to both submissions in this sample; if drafts may omit it, design that separate rule deliberately and test the client and server behavior.",
    "The markup needs no click handler. The complexity moves to server rules and tests for double submissions, stale state, and distinguishing a draft from a final decision.",
    ["Do not assume formaction restricts who can call an endpoint.", "Do not leave two submit buttons with indistinguishable labels.", "Do not accidentally relax validation for a final action."],
    ["html/forms-get-post", "html/form-ownership", "html/form-validation"])

add("reset-button", "forms", "HTML reset button: restore initial form values, not a saved record",
    "A reset button returns form controls to their initial values as represented by the document.",
    "An editor starts with a server-rendered note and changes it locally. Reset discards those unsaved edits and returns to the initial note; it does not fetch the latest server value, erase a saved record, or ask for confirmation. That makes the control risky in long forms. Where an accidental reset would lose substantial work, a clearly named cancel path is often the safer product decision.",
    '''<form action="/receipts/R-47/note" method="post">
  <label for="receipt-note">Internal note</label>
  <textarea id="receipt-note" name="note">Review the disputed line item.</textarea>
  <button type="submit">Save note</button>
  <button type="reset">Restore initial note</button>
</form>''',
    "The initial value is the text inside textarea in this response. If the server record changes after render, reset will not retrieve it. The save endpoint still validates ownership and the submitted note.",
    "Reset itself is cheap and native. Its cost is user error and lost work, particularly when a large form puts reset near submit or assigns both controls similar styles.",
    ["Do not label reset as Delete.", "Do not claim it loads the newest server state.", "Do not place a destructive reset next to save without a clear distinction."],
    ["html/select-and-textarea", "html/forms-get-post", "html/submit-button-overrides"])

add("contenteditable-vs-textarea", "forms", "HTML contenteditable versus textarea: choose the data model first",
    "A textarea is a named form control for plain text; contenteditable makes document content editable but does not become a normal form field by itself.",
    "A receipt reviewer needs a short plain-text reason. Textarea submits its value with the form and has established keyboard and label behavior. A rich document editor might justify contenteditable, but then the application must handle focus, selection, paste, serialization, sanitization, and storage. That is a separate product feature, not a style change to an existing field.",
    '''<form action="/receipts/R-47/reason" method="post">
  <label for="reason">Reason for hold</label>
  <textarea id="reason" name="reason" maxlength="240" required></textarea>
  <button type="submit">Save reason</button>
</form>
<p contenteditable="true" spellcheck="true">Scratch notes are not submitted by this form.</p>''',
    "The editable paragraph is only a demonstration of the difference; without explicit application code, its changes are neither persisted nor sent to the endpoint. Avoid presenting such an area as a real saved note.",
    "Textarea keeps the interaction small. A rich editor adds code, sanitation policy, and security review, with cost proportional to document size and supported editing operations.",
    ["Do not assume contenteditable contributes a name/value pair.", "Do not store pasted HTML without a defined trust boundary.", "Do not replace a plain-text field with a rich editor without a need."],
    ["html/form-labels", "html/select-and-textarea", "html/character-references"])

add("image-loading-priority", "media", "HTML image loading: distinguish a key image from below-fold media",
    "Loading and fetch-priority attributes can influence when image requests start, while width and height reserve layout space.",
    "A receipt detail page shows a small primary mark at the top and an archival scan farther down. The mark is loaded eagerly and marked high priority only if measurement confirms it matters to first paint. The scan can wait until the reader approaches it. Both declare intrinsic dimensions, so the page can allocate space before bytes arrive.",
    '''<main>
  <h1>Receipt R-47</h1>
  <img src="/media/receipt-mark-47.webp" alt="Approved receipt mark" width="320" height="180" loading="eager" fetchpriority="high">
  <section aria-labelledby="scan-heading">
    <h2 id="scan-heading">Archived scan</h2>
    <img src="/media/receipt-scan-47.webp" alt="Scanned receipt R-47" width="960" height="1280" loading="lazy" decoding="async">
  </section>
</main>''',
    "The files and alternatives must exist. Lazy loading is a browser hint, not a guarantee that a request will never start early. A first-screen image should not be lazy merely because most other images are.",
    "The bytes and decode work dominate cost. Measure whether high priority improves the target page; competing high-priority requests can delay styles or other key content.",
    ["Do not set high priority on every image.", "Do not lazy-load a key first-screen image by habit.", "Do not omit dimensions when they are known."],
    ["html/image-alt", "html/responsive-images", "html/resource-hints"])

add("iframe-srcdoc-boundary", "media", "HTML iframe srcdoc: isolate a small preview deliberately",
    "An iframe with srcdoc contains a nested document supplied by an attribute, with its own browsing context and security rules.",
    "A receipt editor previews a tiny static notice before publication. The srcdoc value is trusted, fixed markup in this example, not a string built from user input. An empty sandbox applies restrictions to the nested document, and title gives the frame a useful name. A preview that needs scripts or form submission should receive only the minimum permissions required after a separate threat review.",
    '''<iframe
  title="Receipt notice preview"
  sandbox=""
  width="480"
  height="180"
  srcdoc="&lt;!doctype html&gt;&lt;html lang='en'&gt;&lt;body&gt;&lt;p&gt;Receipt R-47 is awaiting review.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;">
</iframe>''',
    "Do not concatenate untrusted HTML into srcdoc. The sandbox is not a sanitizer; unsafe markup still needs a controlled input and output policy. The frame's size is an initial viewport, not a promise that its contents will fit.",
    "Each frame adds a document, layout work, and isolation overhead. Many previews can be expensive; reuse a single frame or render safe static text when isolation is unnecessary.",
    ["Do not treat sandbox as HTML sanitization.", "Do not combine permissions without reviewing their interaction.", "Do not omit a descriptive frame title."],
    ["html/iframe-sandbox", "html/character-references", "html/document-skeleton"])

add("video-source-fallback", "media", "HTML video sources: declare formats and a real text alternative",
    "A video element can contain source candidates that let the browser choose a format it supports.",
    "A receipt-training clip is encoded in two files. Source elements name each type so the browser can select a playable resource. Captions cover speech and important sounds; a nearby transcript gives another way to inspect the procedure. The source order is a preference, not a transcoding service. If neither file is playable, the fallback text should direct readers to the written instructions.",
    '''<section aria-labelledby="training-heading">
  <h2 id="training-heading">Receipt review training</h2>
  <video controls preload="metadata" width="640" height="360" poster="/media/review-poster-47.webp">
    <source src="/media/review-47.webm" type="video/webm">
    <source src="/media/review-47.mp4" type="video/mp4">
    <track kind="captions" src="/media/review-47.en.vtt" srclang="en" label="English">
    <p>Read the written review procedure below.</p>
  </video>
  <p>Written procedure: verify the ID, inspect the amount, then record a decision.</p>
</section>''',
    "All local media files must be deployed together, and the captions must match the final audio. The poster is a visual cue, not a replacement for captions or the written procedure.",
    "Two encodings increase storage and delivery bytes. The browser normally fetches one chosen media stream, while metadata and poster requests still cost network time.",
    ["Do not assume source elements generate missing formats.", "Do not publish captions from an older cut of the video.", "Do not autoplay instructional media without a user request."],
    ["html/video-captions", "html/audio-controls", "html/figure-and-caption"])

add("skip-link", "accessibility", "HTML skip link: reach main content before repeated navigation",
    "A skip link is an ordinary anchor placed before repeated navigation and targeted at the main content region.",
    "A receipt dashboard has a long set of site links on every page. The first keyboard stop lets a reader jump directly to the current task. The destination ID is unique and sits on main. CSS may visually tuck the link away until focus, but it must remain keyboard reachable and visibly appear when focused; hiding it permanently defeats the purpose.",
    '''<a href="#main-content">Skip to receipt content</a>
<header>
  <nav aria-label="Site"><a href="/receipts">Receipt index</a></nav>
</header>
<main id="main-content">
  <h1>Receipt R-47</h1>
  <p>Review state: pending.</p>
</main>''',
    "The index route must exist. A fragment jump is not a substitute for a sensible heading structure, and focus behavior should be tested in the browsers your users actually use.",
    "The anchor adds almost no transfer or runtime cost. It saves repeated keyboard actions, especially on pages whose navigation expands over time.",
    ["Do not put the skip link after the long navigation.", "Do not target a missing or duplicate ID.", "Do not make the link invisible while it has keyboard focus."],
    ["html/landmarks", "html/anchors-and-paths", "html/focus-and-native-controls"])

add("live-status", "accessibility", "HTML status region: announce a changed result without stealing focus",
    "A status region is a live announcement target for nonurgent changes to an interface.",
    "A receipt search updates results after a request. Keep the status node in the document from the start, then update its text when the request succeeds or fails. The role tells compatible assistive technology that the new message matters without moving keyboard focus away from the search field. A static initial string alone is not a request result and should not pretend that a search ran.",
    '''<form action="/receipts/search" method="get">
  <label for="receipt-query">Find a receipt</label>
  <input id="receipt-query" name="query" type="search">
  <button type="submit">Search</button>
</form>
<p id="receipt-status" role="status"></p>''',
    "The markup establishes a region; it does not fetch results or fill it. A working client must update the text, and a server-rendered search should include a visible result heading or summary after navigation.",
    "A single short region is cheap. Repeated rapid announcements can overwhelm users, so report meaningful outcomes instead of every network or keystroke event.",
    ["Do not place a stale success message in an empty status node.", "Do not move focus for every minor result update.", "Do not rely on status text as the only visible result."],
    ["html/form-labels", "html/focus-and-native-controls", "html/hidden-and-inert"])

add("noscript-fallback", "accessibility", "HTML noscript: keep the essential task available without enhancement",
    "A noscript element provides fallback content when scripting is unavailable in the relevant context.",
    "A receipt list can be rendered by the server as ordinary links. Script may add filtering, but the core record route still works without it. The fallback tells readers which enhancement is missing and where the basic route is. It does not create an offline cache, bypass authentication, or run a substitute service. Keep the message short and action-oriented.",
    '''<main>
  <h1>Receipts</h1>
  <p><a href="/receipts/R-47">Open receipt R-47</a></p>
  <noscript>
    <p>Live filters are unavailable. Use the receipt links above.</p>
  </noscript>
</main>
<script type="module" src="/assets/receipt-filter.js"></script>''',
    "The record and script paths are application assets that must exist. A script may also fail after loading while noscript remains hidden; essential content must therefore stand on its own before enhancement.",
    "Server-rendered links add small HTML weight. They can remove the need for a client request before a reader reaches the task, while the optional filter script adds transfer and execution cost.",
    ["Do not make core links appear only after script execution.", "Do not assume noscript appears when a loaded script throws.", "Do not publish fallback links that lead to missing routes."],
    ["html/script-loading", "html/anchors-and-paths", "html/document-skeleton"])

add("native-popover", "advanced", "HTML popover: show dismissible nonmodal help with a button",
    "The popover attribute gives an element browser-managed show and hide behavior; a button can target it by ID.",
    "A reviewer needs a short explanation of a hold code without leaving the form. The help panel is nonmodal, so the rest of the page remains available. Auto popovers can be dismissed by clicking elsewhere or making a close request. The trigger is placed next to the panel in source order, which makes their relationship easier to follow when the interface changes.",
    '''<button type="button" popovertarget="hold-help">What does hold mean?</button>
<section id="hold-help" popover="auto" aria-labelledby="hold-help-heading">
  <h2 id="hold-help-heading">Hold a receipt</h2>
  <p>A held receipt stays out of export until a reviewer resolves it.</p>
</section>''',
    "A popover does not block background interaction or impose the focus behavior of a modal dialog. Test browser support and keyboard operation for your audience, and retain the meaning in ordinary page text when help is essential to completion.",
    "Native toggling avoids a custom click-away handler. The panel still adds DOM and may need positioning CSS; long or destructive workflows belong in a different interface.",
    ["Do not use a popover as a modal confirmation.", "Do not point popovertarget at a missing ID.", "Do not hide indispensable instructions only inside optional help."],
    ["html/dialog-vs-popover", "html/dialog-and-details", "html/focus-and-native-controls"])

add("custom-elements", "advanced", "HTML custom elements: preserve useful text before upgrade",
    "An autonomous custom element uses a registered hyphenated name and can acquire behavior when its defining script runs.",
    "A receipt status badge starts as readable text inside a custom tag. If the local module loads, it may register the name and enhance the presentation. If the script is delayed or unavailable, the text still communicates the review state. The element name is not a service endpoint, an accessibility role, or a guarantee that a component has been registered.",
    '''<main>
  <h1>Receipt R-47</h1>
  <p>Status: <receipt-status state="held">Held for review</receipt-status></p>
</main>
<script type="module" src="/assets/receipt-status.js"></script>''',
    "The module must exist and define the element once. Its implementation must preserve the meaningful light-DOM text or provide an equivalent accessible status; HTML alone supplies only the fallback state shown here.",
    "The unupgraded element is cheap markup. Upgrade code, styles, and per-instance lifecycle work add cost, so measure a page with many badges before moving simple text into a component system.",
    ["Do not use a name without a hyphen for an autonomous element.", "Do not clear useful fallback text during upgrade.", "Do not assume registration adds form or keyboard semantics."],
    ["html/declarative-shadow-dom", "html/script-modules", "html/live-status"])

add("declarative-shadow-dom", "advanced", "HTML declarative shadow DOM: parse a component boundary from markup",
    "A template with shadowrootmode can create a shadow root on its parent during HTML parsing.",
    "A receipt card has internal structure and a named title slot, while the surrounding page supplies the actual receipt title. The template is parsed as a shadow root rather than shown as a spare fragment. The light-DOM heading remains the semantic content; the component boundary organizes styling and distribution. This is useful only when the component genuinely needs encapsulation.",
    '''<receipt-card>
  <template shadowrootmode="open">
    <article>
      <header><slot name="title">Receipt</slot></header>
      <slot></slot>
    </article>
  </template>
  <h2 slot="title">Receipt R-47</h2>
  <p>Held for review.</p>
</receipt-card>''',
    "Declarative shadow roots depend on the HTML parser path; inserting this string through a generic HTML assignment does not necessarily create the same tree. The custom element name can remain unregistered while the parser handles the shadow root, but any interactive behavior still needs implementation.",
    "Shadow DOM adds a tree and styling boundary per instance. Repeating large templates on a list of hundreds of cards can expand the response, so compare it with plain semantic markup first.",
    ["Do not expect every string-to-DOM operation to activate a declarative shadow root.", "Do not put essential text only inside a hidden fallback.", "Do not add encapsulation where ordinary CSS scoping is enough."],
    ["html/slots-and-fallback", "html/custom-elements", "html/template-inert-markup"])

add("slots-and-fallback", "advanced", "HTML slots: assign light-DOM content and keep a fallback",
    "A slot is a distribution point inside a shadow tree; matching light-DOM children are rendered there.",
    "A receipt card accepts a title from its parent page. The named slot falls back to a generic label only when the parent supplies no matching child. The default slot receives the summary paragraph. This separation is about content ownership: the page owns the record text, while the card owns its reusable frame. Duplicate slot names or missing assignments can place content in an unexpected position.",
    '''<receipt-card>
  <template shadowrootmode="open">
    <article>
      <header><slot name="title">Receipt details</slot></header>
      <slot>Record summary unavailable.</slot>
    </article>
  </template>
  <h2 slot="title">Receipt R-47</h2>
  <p>Review due before the next export batch.</p>
</receipt-card>''',
    "The fallback does not verify that the record data is complete. A server still supplies the correct title and summary, and an enhanced component still needs accessible behavior if it adds controls.",
    "Slot distribution is browser work, not a network request. Complex component trees add styling and debugging cost; keep the light-DOM content meaningful when a component fails to upgrade.",
    ["Do not confuse slot assignment with form submission.", "Do not expect fallback to appear when assigned content exists.", "Do not ship a card whose only useful text depends on a script."],
    ["html/declarative-shadow-dom", "html/custom-elements", "html/sections-and-articles"])

add("canvas-fallback", "advanced", "HTML canvas: draw a chart without hiding its underlying data",
    "A canvas provides a bitmap drawing surface; it does not create semantic data relationships for the marks drawn into it.",
    "A receipt dashboard draws a small trend line for quick scanning. Its width and height set the bitmap dimensions, while a nearby data summary states the key value in ordinary text. The canvas fallback sentence appears when canvas is not rendered; it is not a complete replacement for an accessible chart in a browser that does render the bitmap. Keep the source data available outside the drawing.",
    '''<figure>
  <canvas id="review-trend" width="640" height="240">
    Receipt approvals rose from 47 to 73 this period.
  </canvas>
  <figcaption>Approvals rose from 47 to 73; the report data remains available below.</figcaption>
</figure>
<p>Previous period: 47 approved. Current period: 73 approved.</p>
<script type="module" src="/assets/review-trend.js"></script>''',
    "The module must exist and draw from trusted report values. The text values must match the plotted values; this sample does not include the data service or the drawing implementation.",
    "Bitmap work scales with pixel area and redraw frequency. A textual summary is cheap and often serves readers better than an elaborate visual for only two values.",
    ["Do not assume pixels provide table-like relationships.", "Do not rely only on fallback descendants when canvas renders.", "Do not let chart text drift from the plotted dataset."],
    ["html/data-tables", "html/figure-and-caption", "html/script-modules"])

add("script-modules", "advanced", "HTML module scripts: load one module without ordering every classic script",
    "A script with type=module loads a JavaScript module; a nomodule script can provide a separate classic fallback for older engines.",
    "A receipt dashboard needs a small enhancement after the document is parsed. The module path carries the current implementation. The fallback path is an actual separate build, not the same file renamed: a browser that does not support modules may run it instead. Essential receipt content is already present in HTML, so either script can fail without blanking the page.",
    '''<main>
  <h1>Receipt queue</h1>
  <p><a href="/receipts/R-47">Open receipt R-47</a></p>
</main>
<script type="module" src="/assets/receipt-queue.mjs"></script>
<script nomodule src="/assets/receipt-queue-legacy.js"></script>''',
    "Both asset paths must be deployed if both branches are advertised. Modules have their own loading and scope rules; do not assume a global variable from a classic script is available as an imported binding.",
    "Two builds increase maintenance and asset storage. If the supported browser set needs only modules, omit the legacy branch rather than shipping a fallback nobody uses.",
    ["Do not mark a module file as a classic nomodule fallback.", "Do not rely on scripts for the page's primary text.", "Do not assume module and classic execution order is interchangeable."],
    ["html/script-loading", "html/noscript-fallback", "javascript/getting-started"])

add("dialog-vs-popover", "comparison", "HTML dialog versus popover: decide whether the task blocks the page",
    "A modal dialog captures a focused task; an auto popover presents nonmodal content that can be dismissed lightly.",
    "Receipt approval may require a deliberate confirmation with a clear cancel path. That task belongs in a modal dialog opened by application behavior, with focus and close behavior tested. A short definition of a status code can sit in a popover beside its trigger. Choosing by visual appearance alone can leave background controls active during a destructive step or trap a reader in a help panel that should be dismissible.",
    '''<button type="button" popovertarget="status-help">Status help</button>
<aside id="status-help" popover="auto">
  <p>Held receipts are excluded from export.</p>
</aside>
<dialog id="approve-dialog" aria-labelledby="approve-title">
  <h2 id="approve-title">Approve receipt R-47?</h2>
  <form method="dialog"><button value="cancel">Cancel</button></form>
</dialog>''',
    "The popover trigger works through HTML. The dialog remains closed until code calls its modal opening method; method=dialog closes it and does not submit an approval to a server. A real approval requires a separate authenticated action.",
    "Native primitives reduce hand-written focus and dismissal code, but a modal workflow still needs testing for focus return, errors, and backend state changes.",
    ["Do not treat method=dialog as a server POST.", "Do not use a nonmodal popover for a blocking decision.", "Do not show a dialog merely by setting open and assume it is modal."],
    ["html/native-popover", "html/dialog-and-details", "html/receipt-review-form-project"])

add("receipt-dashboard-project", "project", "HTML receipt dashboard project: readable before enhancement",
    "A server-rendered dashboard can combine a skip link, native navigation, a status table, and optional script without making content depend on JavaScript.",
    "The finance team needs one page for scanning receipt state. The source order starts with a skip link, then a compact navigation region and one main heading. A captioned table carries the record relationship. A module may add filtering later, but the source page already contains a record link and the key number, so a failed script cannot erase the only route to the receipt.",
    '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Receipt dashboard | AI Trove</title>
</head>
<body>
  <a href="#content">Skip to dashboard</a>
  <header><nav aria-label="Receipt navigation"><a href="/receipts">All receipts</a></nav></header>
  <main id="content">
    <h1>Receipt dashboard</h1>
    <table>
      <caption>Current review queue</caption>
      <thead><tr><th scope="col">Receipt</th><th scope="col">State</th></tr></thead>
      <tbody><tr><th scope="row"><a href="/receipts/R-47">R-47</a></th><td>Held</td></tr></tbody>
    </table>
  </main>
  <script type="module" src="/assets/dashboard-filter.js"></script>
</body>
</html>''',
    "The routes and module must be provided by the application. The HTML is a document prototype, not a deployed dashboard service; a real page also needs server data, access control, error states, and an update path for stale rows.",
    "The initial table can be fast for a modest queue. As row count grows, server pagination avoids transferring and laying out thousands of records merely to show the first screen.",
    ["Do not wait for script execution to reveal the only receipt links.", "Do not publish static sample state as live finance data.", "Do not omit focus visibility for the skip link."],
    ["html/skip-link", "html/data-tables", "html/script-modules", "html/receipt-index-project"])


new_paths = {"html/" + draft[0] for draft in drafts}
assert not new_paths.intersection(by_path), "one of the advanced lessons already exists"
assert all(set(draft[-1]) <= set(by_path) | new_paths for draft in drafts), "broken editorial target"

advanced_path = "html/html-tutorial/advanced"
assert advanced_path not in by_path
advanced_hub = copy.deepcopy(by_path["html/html-tutorial/semantics"])
advanced_hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + advanced_path)),
                    path=advanced_path, title="Advanced HTML", subject="html-advanced",
                    summary="Browser parsing, nonmodal UI, components, shadow trees, and graphics.",
                    tags=["html", "advanced"], sort_order=120,
                    created_at=stamp, updated_at=stamp, published_at=stamp)
advanced_hub["data"] = {"subject_root": "html/html-tutorial", "section_path": advanced_path,
                        "content_format": "html", "author_path": "authors/aitrove-editorial",
                        "seo_ready": True, "modules": []}
rows.append(advanced_hub)
by_path[advanced_path] = advanced_hub
root_hub = by_path["html/html-tutorial"]
root_hub["data"]["resource_tabs"].append({"title": "Advanced HTML", "path": advanced_path})
root_hub["body"] += '<p><a href="/' + advanced_path + '">Advanced HTML</a> covers the parser, browser-managed UI, component boundaries, and graphics with explicit fallback rules.</p>'


def body_for(draft):
    slug, section, title, definition, case, sample, boundary, cost, mistakes, links = draft
    title_for = {path: row["title"] for path, row in by_path.items()}
    title_for.update({"html/" + item[0]: item[2] for item in drafts})
    return (
        "<p>" + html.escape(definition) + "</p>"
        "<h2>Use it for a real task</h2><p>" + html.escape(case) + "</p>"
        '<pre><code class="language-html">' + html.escape(sample, quote=False) + "</code></pre>"
        "<h2>What the markup guarantees</h2><p>" + html.escape(boundary) + "</p>"
        "<h2>Cost and limits</h2><p>" + html.escape(cost) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(m) + "</li>" for m in mistakes) + "</ul>"
        "<h2>Connected lessons</h2><ul>" + "".join(
            '<li><a href="/' + target + '">' + html.escape(title_for[target]) + "</a></li>" for target in links
        ) + "</ul>"
    )


by_section = {}
for index, draft in enumerate(drafts):
    slug, section, title, definition, _, _, _, _, _, links = draft
    path = "html/" + slug
    hub_path = "html/html-tutorial" if section == "core" else "html/html-tutorial/" + section
    hub = by_path[hub_path]
    row = copy.deepcopy(by_path["html/document-skeleton"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=title, summary=definition, body=body_for(draft),
               subject=hub["subject"], tags=["html", section],
               sort_order=1400 + index, created_at=stamp, updated_at=stamp, published_at=stamp)
    row["data"] = {"subject_root": "html/html-tutorial", "section_path": hub_path,
                   "content_format": "html", "kind": "project" if section == "project" else "tutorial",
                   "reading_minutes": 7, "author_path": "authors/aitrove-editorial", "seo_ready": True,
                   "related": [{"path": target, "title": by_path[target]["title"] if target in by_path else
                               next(item[2] for item in drafts if "html/" + item[0] == target)} for target in links]}
    rows.append(row)
    by_path[path] = row
    by_section.setdefault(section, []).append(path)

for section, paths in by_section.items():
    hub_path = "html/html-tutorial" if section == "core" else "html/html-tutorial/" + section
    hub = by_path[hub_path]
    if section == "advanced":
        groups = [
            ("Browser-managed UI", ["html/native-popover"]),
            ("Component boundaries", ["html/custom-elements", "html/declarative-shadow-dom", "html/slots-and-fallback"]),
            ("Graphics and loading", ["html/canvas-fallback", "html/script-modules"]),
        ]
    else:
        groups = [("Further " + section + " contracts", paths)]
    for title, targets in groups:
        hub["data"]["modules"].append({"title": title, "summary": "Practical markup choices with failure boundaries.",
                                       "lessons": targets})
    additions = "<h2>Further reading</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths
    ) + "</ul>"
    marker = "<h3>Common Mistakes</h3>"
    if marker in hub["body"]:
        hub["body"] = hub["body"].replace(marker, additions + marker, 1)
    else:
        hub["body"] += additions
    hub["updated_at"] = stamp

advanced_hub["body"] = (
    "<p>These pages cover browser behavior that becomes important when a document gains embedded interfaces or component boundaries. Start from a readable document and add each behavior for a specific task.</p>"
    "<h2>Advanced learning path</h2><ul>"
    + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
              for path in by_section["advanced"])
    + "</ul><p><a href=\"/html/html-tutorial\">Return to the HTML tutorial</a>.</p>"
    "<h3>Common Mistakes</h3><p>A browser primitive still needs real assets, server checks, and fallback content when the task requires them.</p>"
)

for draft in drafts:
    path = "html/" + draft[0]
    first = draft[-1][0]
    if by_path[first]["type"] == "article":
        target = by_path[first]
        link = '<p><a href="/' + path + '">Related: ' + html.escape(by_path[path]["title"]) + "</a>.</p>"
        if ('href="/' + path + '"') not in target["body"]:
            target["body"] += link
            target["data"].setdefault("related", []).append({"path": path, "title": by_path[path]["title"]})
            target["updated_at"] = stamp

questions = [
    ("What can a base element change?", "Resolution of relative fragment and asset URLs", "Only CSS class names", "Only the page title", "A document base applies to relative URLs throughout that document."),
    ("Does preload make an image file smaller?", "No", "Yes", "Only when lazy", "Preload changes request timing, not transferred bytes."),
    ("Does a download attribute authorize a private file?", "No", "Yes", "Only on the same origin", "The server must check access to the resource."),
    ("What must each token in a complex table cell's headers attribute identify?", "A th ID in that table", "A CSS class", "A nearby paragraph", "Explicit header references point to header cells."),
    ("What does a reset button restore?", "The form's initial values", "The newest server record", "An empty form in all cases", "Reset returns controls to their document defaults."),
    ("Does contenteditable become a named form field automatically?", "No", "Yes", "Only on POST", "Editing a paragraph does not make it a successful form control."),
    ("Should a key first-screen image usually be marked lazy by habit?", "No", "Yes", "Only if it has alt text", "Deferring a key image can delay visible content."),
    ("Does an iframe sandbox sanitize untrusted srcdoc markup?", "No", "Yes", "Only with a title", "Isolation and content sanitization solve different problems."),
    ("Is an auto popover a modal confirmation dialog?", "No", "Yes", "Only when it contains a button", "A popover leaves background interaction available."),
    ("Where does a declarative shadow root come from?", "A parsed template with shadowrootmode", "A class attribute", "A CSS pseudo-element", "The parser attaches the shadow root to the template's parent."),
    ("Does canvas drawing supply semantic table relationships?", "No", "Yes", "Only when scaled", "Keep important data in real text or table markup."),
    ("Does method=dialog send an approval POST?", "No", "Yes", "Only with a value attribute", "It closes the dialog; a separate server action changes data."),
]

quiz_path = "quizzes/html-advanced-contracts"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/html-forms-and-accessibility"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Advanced HTML contracts quiz",
            summary="Twelve explained checks on browser primitives and their application limits.",
            subject="html-quizzes", sort_order=3100,
            created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["body"] = (
    "<p>Check whether each HTML primitive actually provides the behavior a feature needs.</p>"
    "<h2>Review the contracts</h2><ul>"
    + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
              for path in ["html/base-element-paths", "html/complex-table-headers", "html/native-popover",
                           "html/declarative-shadow-dom", "html/canvas-fallback", "html/dialog-vs-popover"])
    + "</ul><h3>Common Mistakes</h3><p>Markup never creates missing server routes, assets, permissions, or saved state.</p>"
)
quiz["data"] = {"subject_root": "html/html-tutorial", "section_path": "html/quizzes",
                "content_format": "html", "author_path": "authors/aitrove-editorial",
                "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": path, "title": by_path[path]["title"]} for path in by_section["advanced"]],
                "questions": []}
for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions):
    options = [correct, wrong_a, wrong_b]
    options = options[index % 3:] + options[:index % 3]
    quiz["data"]["questions"].append({"prompt": prompt, "options": options,
                                         "answer": options.index(correct), "explanation": explanation})
rows.append(quiz)
by_path[quiz_path] = quiz
quiz_hub = by_path["html/quizzes"]
quiz_hub["data"]["modules"].append({"title": quiz["title"], "summary": quiz["summary"],
                                      "lessons": [quiz_path]})
quiz_hub["body"] = quiz_hub["body"].replace(
    "</ul>", '<li><a href="/' + quiz_path + '">' + quiz["title"] + "</a></li></ul>", 1
)
advanced_hub["body"] += '<p><a href="/' + quiz_path + '">Check the advanced HTML contracts</a>.</p>'
root_hub["body"] += '<p><a href="/' + quiz_path + '">Check the advanced HTML contracts</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(drafts), "articles, one hub, one quiz bank")

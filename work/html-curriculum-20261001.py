"""Build original, internally linked HTML tutorials from checked editorial cases."""

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


def add(slug, section, title, definition, scenario, code, consequence, cost, mistakes, links):
    lessons.append(dict(slug=slug, section=section, title=title, definition=definition,
                        scenario=scenario, code=code, consequence=consequence,
                        cost=cost, mistakes=mistakes, links=links))


add("document-skeleton", "core", "HTML document skeleton: declare language, encoding, and a real title",
    "An HTML document has a doctype, a root element, metadata in head, and rendered content in body.",
    "A receipt archive can be opened in a browser without a framework. The document declares English for pronunciation and translation, UTF-8 before visible text, and a title that identifies the page in tabs and history. The viewport declaration permits the layout to use the device width; it does not make a fixed-width design responsive by itself.",
    '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Receipt archive | AI Trove</title>
</head>
<body>
  <main>
    <h1>Receipt archive</h1>
    <p>Review issued receipts before exporting a batch.</p>
  </main>
</body>
</html>''',
    "The first heading names the visible page; title names the document when it is seen outside the page. They can differ. Put meaningful content in body and keep one main landmark for the primary task.",
    "A small static document needs no script or build step. Referenced CSS, images, and scripts add their own requests and failure paths; add them only for a concrete need.",
    ["Do not omit the title and expect the heading to fill browser history.", "Declare the page language rather than assuming the browser infers it.", "A viewport meta tag cannot repair overflowing fixed-width content."],
    ["html/metadata-title", "html/landmarks", "css/responsive-layout"])

add("metadata-title", "core", "HTML title and metadata: distinguish document identity from page copy",
    "The title element names a document in browser UI, while meta elements carry machine-readable document metadata.",
    "The receipt list is one page in a larger site. Its title includes the page purpose and site name; its description gives a short human-readable summary. A page-specific description is useful for previews, but a search engine may choose different text. The charset declaration stays near the start of head so decoding is settled early.",
    '''<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pending receipts | AI Trove</title>
  <meta name="description" content="Review pending receipt batches and export dates.">
</head>''',
    "Keep exactly one meaningful title for an ordinary document. Metadata is not a substitute for the visible heading or for access control: anything emitted into the response is available to the client.",
    "Metadata adds little transfer size, but duplicate or stale descriptions create maintenance cost across many routes. Generate them from the page's actual purpose, then inspect the rendered head.",
    ["Do not put a secret or private token in a meta element.", "Avoid giving many unrelated pages the same title.", "The description does not guarantee the text shown in a search result."],
    ["html/document-skeleton", "html/headings-and-paragraphs", "web-tech/web-technology"])

add("headings-and-paragraphs", "core", "HTML headings and paragraphs: expose a readable outline without styling tricks",
    "Heading elements identify sections of content; paragraphs group prose under those sections.",
    "A finance page starts with one page heading and then splits review and export work into peer sections. Choose heading levels from the document hierarchy, not from font size. CSS may change their appearance while the DOM keeps the same reading order for keyboard and assistive-technology users.",
    '''<main>
  <h1>Receipt operations</h1>
  <section aria-labelledby="review-heading">
    <h2 id="review-heading">Review</h2>
    <p>Check the batch total before approval.</p>
  </section>
  <section aria-labelledby="export-heading">
    <h2 id="export-heading">Export</h2>
    <p>Download only approved receipts.</p>
  </section>
</main>''',
    "A section with an accessible heading has a clear purpose. The h2 elements are siblings under the h1; neither is a smaller heading merely because it looks smaller on screen.",
    "Semantic headings cost no script or network request. Misusing them can make long pages harder to scan, particularly when a styled div looks like a heading but is absent from heading navigation.",
    ["Do not skip levels to get a preferred font size.", "Do not use an empty heading as a spacer.", "Keep DOM order meaningful before visual reordering."],
    ["html/document-skeleton", "html/sections-and-articles", "html/landmarks"])

add("lists-and-definitions", "core", "HTML lists: choose ordered, unordered, or term-description structure",
    "A list element expresses the relationship among items, including whether sequence is meaningful.",
    "Receipt processing has steps whose order matters and properties whose order does not. Use ol for the approval sequence. Use dl for a term and its value when the content is a small set of definitions; do not force key-value data into a visual row of unrelated div elements.",
    '''<h2>Approval sequence</h2>
<ol>
  <li>Verify the receipt ID.</li>
  <li>Check the amount against the ledger.</li>
  <li>Approve the export.</li>
</ol>
<h2>Batch details</h2>
<dl>
  <dt>Batch ID</dt><dd>RB-47</dd>
  <dt>Status</dt><dd>Awaiting review</dd>
</dl>''',
    "The ordered list preserves the process sequence even without CSS. A definition list communicates paired terms and descriptions; for a large cross-referenced data matrix, use a real table instead.",
    "The DOM stays compact. The main cost is editorial: list order, nesting, and labels must stay accurate when a workflow changes.",
    ["Do not make a numbered workflow from plain paragraphs and CSS counters alone.", "Do not put unrelated sections into one list just to align them.", "Use table headers when both rows and columns define values."],
    ["html/data-tables", "html/headings-and-paragraphs", "html/sections-and-articles"])

add("anchors-and-paths", "core", "HTML anchors: use href for navigation and stable fragment targets",
    "An anchor with href creates a link that can be followed, copied, opened in a new tab, and reached by keyboard.",
    "A receipt index links to a specific record and to an explanation lower on the same page. The fragment target is an id on the destination heading. Relative paths keep the example on the same origin, while the visible link text says what will open rather than relying on surrounding text.",
    '''<nav aria-label="Receipt navigation">
  <a href="/receipts/R-47">Open receipt R-47</a>
  <a href="#export-policy">Read the export policy</a>
</nav>
<section aria-labelledby="export-policy">
  <h2 id="export-policy">Export policy</h2>
  <p>Only approved receipts are included.</p>
</section>''',
    "The path route needs a server that serves that record; HTML alone does not create the endpoint. Use a button for a local action such as submitting a form, and use an anchor for navigation.",
    "Links require no JavaScript. Broken paths and duplicate ids are the practical failure modes, so check internal destinations as part of publishing.",
    ["Do not use href='#' as a fake button.", "A fragment id must be unique within its document.", "Describe the destination; repeated 'click here' labels lose context."],
    ["html/link-vs-button", "html/landmarks", "html/document-skeleton"])

add("character-references", "core", "HTML character references: escape data before inserting it into markup",
    "The HTML parser treats less-than signs and ampersands as syntax unless character references represent them as text.",
    "A receipt label is untrusted display data. Its characters belong in a text node, never as a string concatenated into an HTML template. The literal lesson shows how markup text must be represented; application code should use a renderer that escapes data for the exact output context.",
    '''<p>Customer note: 47 &lt; 73 &amp; review remains open.</p>
<p>Attribute value: &quot;pending&quot;</p>''',
    "Escaping for a text node and escaping for a quoted attribute are related but distinct contexts. Do not turn already-escaped data into HTML again or it will show entity text; do not decode received text and then inject it as markup.",
    "Entity parsing is linear in the input length. The larger risk is a trust-boundary bug: treating user text as HTML can create elements or attributes the author never intended.",
    ["Do not build HTML by joining untrusted strings.", "Do not assume URL encoding is HTML escaping.", "Escape at the output boundary rather than mutating the stored value."],
    ["html/anchors-and-paths", "html/forms-get-post", "javascript/core-concepts"])

add("landmarks", "semantics", "HTML landmarks: give navigation, main content, and page edges clear owners",
    "header, nav, main, and footer identify the purpose of page regions without assigning visual layout.",
    "A receipt page has one primary task, a short site navigation, and a separate footer. The nav element gets a label when another navigation region may appear. A skip link lets keyboard users bypass repeated site links and reach the main region directly.",
    '''<a href="#content">Skip to receipt content</a>
<header><p>AI Trove receipts</p></header>
<nav aria-label="Primary">
  <a href="/receipts">Receipts</a>
  <a href="/reports">Reports</a>
</nav>
<main id="content">
  <h1>Pending receipts</h1>
  <p>Review 47 open records.</p>
</main>
<footer><p>Receipt operations desk</p></footer>''',
    "The skip link requires CSS that leaves it available on focus. Landmark elements do not automatically make their links or text accessible; names, focus, and reading order still need review.",
    "Native regions avoid custom role code. Too many unnamed navigation regions can create noisy landmark lists, so name distinct regions by purpose.",
    ["Do not add multiple main elements for separate cards.", "A header inside an article is that article's header, not necessarily the site header.", "Keep the skip target and its id in the same document."],
    ["html/anchors-and-paths", "html/headings-and-paragraphs", "html/focus-and-native-controls"])

add("sections-and-articles", "semantics", "HTML article and section: mark standalone content and named subdivisions",
    "article is content that can stand on its own; section groups related content under a common heading.",
    "A report feed contains independent receipt notices, each with its own heading and status. Inside one notice, a section separates review instructions. A generic wrapper remains appropriate when the grouping exists only for layout; article and section should carry actual content meaning.",
    '''<main>
  <h1>Receipt notices</h1>
  <article aria-labelledby="notice-47">
    <h2 id="notice-47">Receipt R-47 is ready</h2>
    <p>The export window closes at 18:00.</p>
    <section aria-labelledby="review-47">
      <h3 id="review-47">Review steps</h3>
      <p>Confirm the amount before approving.</p>
    </section>
  </article>
</main>''',
    "A screen reader can jump to the article heading, and the nested section has its own name. Nesting does not invent a new heading rank; choose h2 and h3 from the actual document outline.",
    "Semantic wrappers have negligible runtime cost. Maintenance suffers when every styled card becomes an article, because the structure no longer distinguishes reusable content from decoration.",
    ["Do not use section as a generic styling hook.", "Give substantial sections a heading.", "An article can contain sections, but a layout column is not automatically either one."],
    ["html/landmarks", "html/headings-and-paragraphs", "html/figure-and-caption"])

add("figure-and-caption", "semantics", "HTML figure and figcaption: keep an asset with its explanation",
    "figure groups self-contained content with an optional caption that explains its role in the surrounding document.",
    "A monthly receipts chart has an adjacent caption stating the period and unit. Its image alt carries the key finding for someone who cannot inspect the graphic. The caption provides context for everyone; it should not merely repeat the alt text word for word.",
    '''<figure>
  <img src="/media/receipt-volume-2026.webp"
       width="640" height="360"
       alt="Receipt volume peaked in March at 47 records">
  <figcaption>Issued receipts by month, January to April 2026.</figcaption>
</figure>''',
    "The media file must exist at the stated path. For a chart with many values, provide the underlying values in nearby text or an accessible data table; a short alt cannot encode an entire series.",
    "Width and height let the browser reserve space before download. The image still has transfer and decode costs; prepare an appropriate size and format instead of shipping a huge original.",
    ["Do not use a caption as a replacement for a meaningful alt.", "Do not write alt that only says 'chart' or repeats the filename.", "Do not put the only data values inside pixels."],
    ["html/image-alt", "html/responsive-images", "html/data-tables"])

add("data-tables", "semantics", "HTML data tables: name row and column relationships explicitly",
    "A table represents data whose cells gain meaning from row and column headers.",
    "A receipt summary compares two regions across amount and state. A caption gives the table a name; scope on th cells keeps simple row and column associations clear. The table is for relationships in the data, not for positioning the surrounding page.",
    '''<table>
  <caption>Receipt review queue</caption>
  <thead><tr><th scope="col">Region</th><th scope="col">Amount</th><th scope="col">State</th></tr></thead>
  <tbody>
    <tr><th scope="row">North</th><td>47 credits</td><td>Pending</td></tr>
    <tr><th scope="row">South</th><td>26 credits</td><td>Approved</td></tr>
  </tbody>
</table>''',
    "A complex table with multi-level headers needs more explicit associations than this simple grid. At narrow widths, permit horizontal scrolling or redesign the data presentation while preserving header relationships.",
    "Rendering a large table creates many DOM nodes. Paginate or summarize large datasets; hiding columns with CSS can also hide important relationships.",
    ["Do not use a table for page layout.", "Use th for headers rather than bold td text.", "A caption identifies the table; it does not replace row and column headers."],
    ["html/lists-and-definitions", "html/table-vs-layout", "html/figure-and-caption"])

add("time-and-machine-values", "semantics", "HTML time and data: pair readable copy with machine-readable values",
    "time can carry a machine-readable date or time, while data can attach a machine-readable value to visible text.",
    "The receipt page shows a localized review deadline while keeping an ISO-formatted dateTime attribute for parsers. Its state label also carries a stable code. Neither attribute validates a business rule; the application must still decide when the deadline expires and who can approve.",
    '''<p>Review by <time datetime="2026-10-23">23 October 2026</time>.</p>
<p>Status: <data value="awaiting-review">Awaiting review</data>.</p>''',
    "The visible date must agree with datetime. If the deadline includes a time zone, include the offset in the machine value and explain the local time to the reader; a bare calendar date is not a universal instant.",
    "These attributes cost almost nothing to render. Their maintenance cost is synchronization: changing the visible copy without updating the machine value creates conflicting facts.",
    ["Do not put an incompatible date in datetime.", "A state code in data is metadata, not an authorization check.", "Do not treat a local date as an exact instant without a time zone."],
    ["html/metadata-title", "html/sections-and-articles", "python/datetime-boundaries"])

add("forms-get-post", "forms", "HTML forms: choose GET for retrieval and POST for a state change",
    "A form combines successful named controls into a request using its action and method.",
    "A receipt search is read-only and uses GET so the query can appear in the URL. Approval is a state change and uses POST. These are different endpoint contracts; a browser form does not provide authorization, replay protection, or a server-side validation rule.",
    '''<form action="/receipts/search" method="get">
  <label for="receipt-query">Receipt ID</label>
  <input id="receipt-query" name="receipt" type="search">
  <button type="submit">Search receipts</button>
</form>
<form action="/receipts/approve" method="post">
  <input type="hidden" name="receipt_id" value="R-47">
  <button type="submit">Approve R-47</button>
</form>''',
    "The POST endpoint must authenticate the user, authorize the specific receipt, validate the ID, and apply a request-forgery defense appropriate to its session model. A hidden input can be edited by a client.",
    "Native form submission works without JavaScript and has predictable keyboard behavior. Network and server costs depend on the endpoint and payload, not on the presence of a form element.",
    ["Do not use GET for a destructive action.", "A hidden field is still client input.", "Controls without a name are not submitted as normal form entries."],
    ["html/form-labels", "html/form-names-disabled", "html/form-validation"])

add("form-labels", "forms", "HTML labels: bind each control to a durable accessible name",
    "A label gives a form control a visible name and a larger activation target.",
    "The receipt ID field uses for and id so the label remains associated even if layout wrappers are added. Helper text gets its own id and is referenced by aria-describedby. A placeholder may show an input hint, but it disappears or changes during editing and should not carry the only name.",
    '''<label for="receipt-id">Receipt ID</label>
<input id="receipt-id" name="receipt_id" type="text"
       autocomplete="off" aria-describedby="receipt-hint">
<p id="receipt-hint">Use the code printed at the top of the receipt.</p>''',
    "The server still needs to validate the received ID. Avoid duplicate ids across repeated form rows; an explicit label may then point at the wrong control.",
    "A correct label adds no script cost and makes click and touch targets more forgiving. The main maintenance risk is renaming an id without updating for or aria-describedby.",
    ["Do not use placeholder as the sole label.", "Keep for equal to one unique control id.", "A visual heading near a field does not automatically name that field."],
    ["html/forms-get-post", "html/form-validation", "html/focus-and-native-controls"])

add("form-names-disabled", "forms", "HTML form names and disabled controls: know which values submit",
    "The name attribute identifies a submitted entry; disabled controls are excluded from normal form submission.",
    "The reviewer can inspect a locked batch ID, but disabling that field also means the server will not receive it from that control. A separate hidden field can carry the ID, though the server must treat it as untrusted. A readonly text field stays focusable and may be submitted, which is a different interaction contract.",
    '''<form action="/receipts/review" method="post">
  <label for="batch-display">Batch ID</label>
  <input id="batch-display" value="RB-47" disabled>
  <input type="hidden" name="batch_id" value="RB-47">
  <label for="review-note">Review note</label>
  <input id="review-note" name="review_note" type="text" required>
  <button type="submit">Save review</button>
</form>''',
    "The server must look up RB-47 and check the current user's permission. A form may contain repeated names, which are legitimate for some controls; decide how an endpoint handles them instead of silently taking one value.",
    "The markup cost is small. The cost of misunderstanding successful controls is a dropped value or an unintended duplicate at the server boundary.",
    ["Do not assume an input without name is sent.", "Disabled is not the same as readonly.", "Never authorize an action from a hidden value alone."],
    ["html/forms-get-post", "html/form-validation", "html/radio-checkbox"])

add("form-validation", "forms", "HTML constraint validation: improve feedback without trusting the browser",
    "Attributes such as required, minlength, and type constrain interactive form input before ordinary submission.",
    "A receipt address field asks for an email-shaped value and a note of bounded length. The browser can prompt users early. The backend must repeat every relevant validation rule because callers can send HTTP requests without using this form or can modify its markup.",
    '''<form action="/receipts/notify" method="post">
  <label for="recipient-email">Recipient email</label>
  <input id="recipient-email" name="email" type="email" required>
  <label for="review-reason">Review reason</label>
  <input id="review-reason" name="reason" type="text"
         minlength="8" maxlength="120" required>
  <button type="submit">Queue notice</button>
</form>''',
    "Client validation does not prove the mailbox exists or the sender may contact it. Error messages, focus order, and server rejection still need design. A length limit here counts form-control input according to browser rules, not necessarily the backend's storage bytes.",
    "Native checks avoid an extra JavaScript dependency for basic cases. Complex custom validation increases code and can reduce accessibility if errors are not tied to their fields.",
    ["Do not treat required as a server-side security rule.", "An email input checks syntax, not delivery.", "Avoid removing native validation unless a replacement supplies comparable feedback."],
    ["html/forms-get-post", "html/form-labels", "html/required-vs-aria-required"])

add("radio-checkbox", "forms", "HTML radio and checkbox controls: submit choices with explicit values",
    "Radio buttons with one name select one option; checkboxes represent independent on-or-off selections.",
    "A receipt review selects one disposition and may independently request a copy. Each control has a label and explicit value. The fieldset and legend name the radio group, so the options have context when reached out of visual order.",
    '''<form action="/receipts/review" method="post">
  <fieldset>
    <legend>Disposition for R-47</legend>
    <label><input type="radio" name="decision" value="approve" required> Approve</label>
    <label><input type="radio" name="decision" value="hold"> Hold</label>
  </fieldset>
  <label><input type="checkbox" name="send_copy" value="yes"> Send a copy</label>
  <button type="submit">Record decision</button>
</form>''',
    "An unchecked checkbox normally contributes no entry, so the server needs a defined default. The client can still send an unlisted value or both radio values; validate the received set and authorization.",
    "Native grouping handles keyboard interaction without custom controls. Each additional option adds DOM and review work; keep the choice set small enough to scan.",
    ["Do not give radios in one group different names.", "Never infer a missing checkbox entry means the user saw it.", "Define the server's behavior for repeated or unknown choice values."],
    ["html/form-labels", "html/forms-get-post", "html/select-and-textarea"])

add("select-and-textarea", "forms", "HTML select and textarea: preserve meaningful values and editable text",
    "select submits a chosen option value; textarea submits its text content under a name.",
    "A review form makes the initial reason choice intentionally empty, then asks for free-text context. The first option is disabled and selected so the required select cannot quietly send a business decision. The textarea has a visible label and a character limit; server validation still owns the stored record.",
    '''<form action="/receipts/review" method="post">
  <label for="review-reason">Reason</label>
  <select id="review-reason" name="reason" required>
    <option value="" selected disabled>Choose a reason</option>
    <option value="amount-mismatch">Amount mismatch</option>
    <option value="missing-approval">Missing approval</option>
  </select>
  <label for="review-context">Context</label>
  <textarea id="review-context" name="context" maxlength="240"></textarea>
  <button type="submit">Save review</button>
</form>''',
    "Option text is for readers; value is the API input. Keep codes stable when copy changes. A disabled placeholder option does not absolve the server from rejecting an empty or unknown reason.",
    "The controls cost little until option lists become long. Large remote vocabularies may need search, but replacing select with a custom widget adds keyboard and focus obligations.",
    ["Do not make a placeholder a valid business value.", "Do not rely on displayed option text as the stable submitted code.", "Textarea content is text, not trusted HTML."],
    ["html/radio-checkbox", "html/form-validation", "html/form-labels"])

add("file-upload-form", "forms", "HTML file upload forms: declare multipart encoding and bound the server",
    "A file input submits a selected file as part of a multipart form request when the form uses the matching encoding.",
    "A receipt reviewer may attach a supporting document. The form states multipart/form-data and gives the file control a name. accept hints which files to show in the picker; it does not prove the bytes are a PDF, enforce size, or make the file safe to store.",
    '''<form action="/receipts/evidence" method="post" enctype="multipart/form-data">
  <label for="receipt-code">Receipt ID</label>
  <input id="receipt-code" name="receipt_id" value="R-47" required>
  <label for="evidence-file">Supporting document</label>
  <input id="evidence-file" name="evidence" type="file"
         accept="application/pdf" required>
  <button type="submit">Upload evidence</button>
</form>''',
    "The endpoint must limit request and file bytes, validate content, assign its own storage name, and authorize attachment to the chosen receipt. A browser-supplied filename is display metadata, not a safe path.",
    "Uploads can dominate bandwidth, disk, and parsing time. Put size and processing limits at the server boundary before expensive decoding or downstream work.",
    ["accept is a picker hint, not content validation.", "Do not trust receipt_id or the filename from the form.", "Without multipart encoding the file data will not arrive as intended."],
    ["html/forms-get-post", "html/form-validation", "python/flask-multipart-budgets"])

add("image-alt", "media", "HTML image alt text: describe function or information, not pixels alone",
    "The alt attribute supplies text in place of an image when its visual content or function is unavailable.",
    "The first icon acts as the only content of a link, so its alt names the destination. The second image is decorative beside an explicit text label, so an empty alt avoids repeating that label. A receipt chart needs the useful finding in alt and a nearby detailed account if the series matters.",
    '''<a href="/receipts/R-47">
  <img src="/media/receipt-open.svg" width="24" height="24"
       alt="Open receipt R-47">
</a>
<p><img src="/media/checkmark.svg" width="16" height="16" alt="">
   Approved receipt</p>''',
    "The referenced assets are local application files and must exist. Avoid turning a complex chart into a one-sentence alt alone; give the data in adjacent prose or a table. If an image fails to load, meaningful alt should still tell the user what action or information it carried.",
    "Small icons are cheap to transfer, but shipping a large image at icon dimensions wastes bytes. Width and height reserve layout space; prepare an asset at a suitable intrinsic size.",
    ["Do not write 'image of' when the purpose is already clear.", "Do not leave a linked icon without an accessible destination name.", "An empty alt is correct only when the image adds no information or action."],
    ["html/figure-and-caption", "html/responsive-images", "html/anchors-and-paths"])

add("responsive-images", "media", "HTML srcset and sizes: let the browser choose an appropriately sized image",
    "srcset with width descriptors lists candidate files, while sizes estimates the rendered width for source selection.",
    "A receipt chart occupies almost the viewport on a phone and half a wide report on desktop. The sizes value describes that layout; the srcset candidates supply different image widths. The browser combines this information with device conditions when choosing what to fetch.",
    '''<img src="/media/receipt-chart-640.webp"
     srcset="/media/receipt-chart-640.webp 640w,
             /media/receipt-chart-1280.webp 1280w"
     sizes="(max-width: 48rem) 100vw, 50vw"
     width="640" height="360"
     alt="North had 47 reviewed receipts; South had 26">''',
    "The application must actually generate both candidate files with the same content and valid dimensions. sizes is not a CSS rule; if it disagrees with the rendered width, the browser can choose an unnecessarily large file.",
    "More variants require storage and build work, but can cut transfer on small screens. Measure actual rendered widths and byte sizes before adding many breakpoints.",
    ["Do not mix width and pixel-density descriptors in one candidate list.", "Do not omit alt because several image files exist.", "A false sizes value can erase the bandwidth benefit."],
    ["html/image-alt", "html/figure-and-caption", "css/responsive-layout"])

add("picture-art-direction", "media", "HTML picture: switch image composition while keeping one fallback img",
    "picture lets source elements choose different assets by media condition or format before falling back to img.",
    "A wide operations illustration includes context that becomes unreadable on narrow screens. The narrow asset is a separately cropped version, not merely a smaller file. The final img carries the alternative text, fixed dimensions for its fallback, and a source when no source condition matches.",
    '''<picture>
  <source media="(max-width: 42rem)"
          srcset="/media/receipt-flow-portrait.webp">
  <img src="/media/receipt-flow-wide.webp"
       width="960" height="420"
       alt="Receipt review moves from intake to approval and export">
</picture>''',
    "The two assets must communicate the same essential information. Switching crops changes the visible composition; test both against the alt and nearby text. The picture element itself does not replace the img or own its alt.",
    "Art direction creates extra editorial assets and cache entries. Use it when composition truly changes, not as a replacement for srcset's size selection.",
    ["Do not put alt on source and omit it from img.", "Keep the fallback img available.", "Verify that a narrow crop does not remove the information described in the text."],
    ["html/responsive-images", "html/image-alt", "html/figure-and-caption"])

add("video-captions", "media", "HTML video tracks: expose controls and a caption file",
    "video embeds timed media, and a captions track can carry speech and meaningful audio information as text.",
    "A receipt approval walkthrough includes spoken instructions. Native controls allow play and pause without a custom player. The track points to a local WebVTT file, identified as English; the transcript link provides a separate route for readers who need the content without video.",
    '''<figure>
  <video controls preload="metadata" width="640" height="360">
    <source src="/media/receipt-review.mp4" type="video/mp4">
    <track kind="captions" src="/media/receipt-review.en.vtt"
           srclang="en" label="English" default>
    Your browser cannot play this video.
  </video>
  <figcaption>Reviewing a receipt before approval.</figcaption>
</figure>
<a href="/transcripts/receipt-review">Read the walkthrough transcript</a>''',
    "The video, caption, and transcript files are application assets that must be supplied and kept in sync. A caption track with only speech but no relevant sound cues may miss part of the experience; a transcript can include additional visual context.",
    "Video transfer can dwarf the HTML page. preload=metadata limits the initial request intent, but user agents may choose their own loading strategy. Provide a poster or multiple formats when the product needs them.",
    ["Do not ship an empty track just to display a captions control.", "Avoid autoplaying spoken media.", "Native controls do not remove the need for accurate captions and a transcript."],
    ["html/image-alt", "html/figure-and-caption", "html/iframe-sandbox"])

add("iframe-sandbox", "media", "HTML iframe sandbox: isolate an embedded preview and name its purpose",
    "An iframe embeds another browsing context; sandbox restricts what that embedded page can do.",
    "A receipt preview is displayed inside a bounded frame with a title and a sandbox allowing scripts but not same-origin treatment. The preview can run its own script, yet it does not gain the parent page's origin merely because its URL path is local.",
    '''<iframe src="/previews/receipt-R-47.html"
        title="Receipt R-47 preview"
        sandbox="allow-scripts"
        loading="lazy" width="640" height="420"></iframe>''',
    "The preview route must exist and control what it serves. Do not casually combine allow-scripts with allow-same-origin for content on the embedding origin; that pairing can undercut the intended isolation. A sandbox is one defense, not a substitute for escaping received HTML and setting server policies.",
    "A frame loads another document and its dependencies. Reserve its dimensions and defer below-the-fold content when appropriate; a large embedded app can dominate page cost.",
    ["Give each meaningful iframe a title.", "Review every sandbox token as an added capability.", "Do not assume a same-origin path remains same-origin under this sandbox policy."],
    ["html/character-references", "html/document-skeleton", "html/video-captions"])

add("script-loading", "media", "HTML script loading: choose ordered defer or independent async work",
    "defer downloads an external classic script without blocking parsing and runs it after parsing; async runs when its download is ready.",
    "A receipt page needs its UI script after the DOM exists, so it uses defer. A separate analytics script has no dependency on that UI and can use async. This distinction is about execution order, not only speed; an async script can run before or after nearby markup finishes parsing.",
    '''<head>
  <meta charset="utf-8">
  <title>Receipt review</title>
  <script src="/assets/receipt-ui.js" defer></script>
  <script src="/assets/usage-metrics.js" async></script>
</head>''',
    "Both paths must point to trusted files owned by the application. A deferred script can still fail to download or throw during execution; ship useful HTML first so the page is readable when behavior is unavailable.",
    "The HTML stays small while each script adds transfer, parse, and execution cost. A third-party dependency would add an external trust and availability boundary; this example uses only local assets.",
    ["Do not rely on async scripts executing in source order.", "defer on an inline classic script does not provide the same external-loading behavior.", "Do not make basic page text appear only after a script runs."],
    ["html/document-skeleton", "html/landmarks", "javascript/getting-started"])

add("focus-and-native-controls", "accessibility", "HTML focus order: use native controls and keep DOM order usable",
    "Native links, buttons, and form fields participate in keyboard navigation according to their built-in behavior.",
    "A receipt action bar follows the document's reading order: first the record link, then the review button. CSS can arrange them visually, but it should not create a contradictory path for keyboard users. The button has an explicit type so moving it into a form later will not turn it into an accidental submitter.",
    '''<section aria-label="Receipt actions">
  <a href="/receipts/R-47">Read receipt R-47</a>
  <button type="button">Open review panel</button>
</section>''',
    "The panel action requires an implementation if the button is used in a real application; markup alone does not open it. The example shows the correct control shape, not a functioning panel. Preserve a visible focus indicator in CSS.",
    "Native controls avoid a custom keyboard event layer. Positive tabindex values often create maintenance trouble when new controls are inserted, so follow DOM order instead.",
    ["Do not replace a button with a clickable div.", "Do not remove focus outlines without a visible replacement.", "Visual reordering cannot repair a confusing DOM sequence."],
    ["html/link-vs-button", "html/landmarks", "html/form-labels"])

add("hidden-and-inert", "accessibility", "HTML hidden and inert: remove inactive content from interaction deliberately",
    "hidden makes content unavailable for rendering; inert prevents user interaction and focus within a subtree.",
    "A future receipt panel starts hidden, while a separate sample region is visible but inert during a temporary state. The attributes solve different tasks. Inert text is still present in the document source and cannot conceal a secret or enforce a permission boundary.",
    '''<section hidden aria-labelledby="future-heading">
  <h2 id="future-heading">Future receipt settings</h2>
  <p>Available after the next release.</p>
</section>
<section inert aria-labelledby="preview-heading">
  <h2 id="preview-heading">Read-only preview</h2>
  <button type="button">Approve receipt</button>
</section>''',
    "A real state transition must add or remove these attributes when the interface changes. If the preview is meant to be readable and focusable, inert is the wrong choice; use a noninteractive description instead.",
    "These are native browser features with no library cost. The bigger cost is state consistency: hidden or inert content that never becomes available leaves a dead path in the product.",
    ["Do not use hidden or inert to protect confidential data.", "Do not place the only error message inside a hidden subtree.", "A disabled button and an inert region have different scopes."],
    ["html/focus-and-native-controls", "html/dialog-and-details", "html/hidden-vs-aria-hidden"])

add("dialog-and-details", "accessibility", "HTML details and dialog: distinguish disclosure from a modal task",
    "details discloses optional content; dialog represents a dialog box whose behavior depends on how it is opened.",
    "A receipt page uses details for a short policy note. The dialog snippet shows static non-modal content using open, which is useful for demonstrating its structure. A production modal requires an owner to invoke showModal, handle close, and restore focus to the initiating control.",
    '''<details>
  <summary>What appears in the export?</summary>
  <p>Only approved receipts in the selected batch.</p>
</details>
<dialog open aria-labelledby="review-title">
  <h2 id="review-title">Review receipt R-47</h2>
  <p>This open attribute alone does not make the dialog modal.</p>
</dialog>''',
    "Do not treat dialog open as equivalent to a modal focus trap. A dialog launched with JavaScript needs an explicit close path and a tested focus return. For a plain expandable explanation, details is the lighter choice.",
    "details works without an application script. Modal orchestration adds code and interaction testing; choose it only when interruption and focus management are part of the task.",
    ["Do not nest a button in summary just to create disclosure behavior.", "Do not assume open makes a dialog modal.", "Test keyboard close and focus return in a real modal flow."],
    ["html/focus-and-native-controls", "html/hidden-and-inert", "javascript/core-concepts"])

add("language-and-direction", "accessibility", "HTML lang, dir, and bdi: keep text pronunciation and direction stable",
    "lang declares a text language; dir and bdi control how bidirectional text is embedded in surrounding copy.",
    "An English receipt page includes a customer name whose direction may differ from the sentence. Mark the known language on the name and isolate its direction with bdi, so punctuation around the inserted name does not shift unexpectedly. The document-level language still belongs on html.",
    '''<html lang="en">
<body>
  <main>
    <h1>Receipt owner</h1>
    <p>Approved for <bdi lang="ar">ليلى</bdi> on 23 October.</p>
  </main>
</body>
</html>''',
    "If the language is unknown, do not guess it from a person's name. Bidi isolation handles direction interaction; translation and pronunciation still need correct language metadata where known. A fragment inserted by an application should not overwrite the whole page's lang.",
    "The markup has negligible runtime cost. Text-direction bugs tend to appear only with real mixed-language data, so test a few right-to-left names and punctuation cases.",
    ["Do not replace bdi with manual left-to-right marks in every record.", "Set lang where the language actually changes.", "Direction metadata does not translate the content."],
    ["html/document-skeleton", "html/character-references", "html/focus-and-native-controls"])

add("link-vs-button", "comparison", "HTML link versus button: navigation and actions have different contracts",
    "An anchor with href navigates to a resource; a button invokes an action in the current interface or submits a form.",
    "The receipt ID opens another route, so it is a link. Approval submits a POST form, so it is a button. Styling can make the two look similar, but their keyboard behavior, browser context menus, and history semantics remain different.",
    '''<a href="/receipts/R-47">Open receipt R-47</a>
<form action="/receipts/approve" method="post">
  <input type="hidden" name="receipt_id" value="R-47">
  <button type="submit">Approve R-47</button>
</form>''',
    "The approval endpoint must validate identity, current status, and permission. A link to a mutation route makes accidental crawls and prefetches dangerous; a button without a handler does not change the page.",
    "Both are native, low-cost controls. The expensive mistake is semantic drift: custom keyboard code and broken browser behaviors appear when one is styled to imitate the other without using its contract.",
    ["Do not use href='#' as a button substitute.", "Do not make an approval GET link.", "Give both controls descriptive text."],
    ["html/anchors-and-paths", "html/forms-get-post", "html/focus-and-native-controls"])

add("required-vs-aria-required", "comparison", "HTML required versus aria-required: semantics do not replace validation",
    "required participates in a native control's constraint validation; aria-required communicates a requirement to accessibility APIs.",
    "A standard receipt field can use required directly. Adding aria-required to that same native field repeats information and is usually unnecessary. A custom widget might need ARIA state, but it must implement its own input, validation, error, and focus behavior.",
    '''<form action="/receipts/find" method="get">
  <label for="lookup-code">Receipt code</label>
  <input id="lookup-code" name="code" required>
  <button type="submit">Find receipt</button>
</form>''',
    "The server still validates the code, even when the browser refuses an empty ordinary submission. ARIA changes accessibility semantics; it does not enforce a value or turn a custom div into a native input.",
    "Using the native attribute avoids a parallel validation implementation. A custom control raises testing cost across keyboard, touch, assistive technology, and browser validation states.",
    ["Do not assume aria-required blocks form submission.", "Do not add redundant ARIA where the native attribute already supplies the state.", "Keep server validation independent of browser markup."],
    ["html/form-validation", "html/form-labels", "html/focus-and-native-controls"])

add("hidden-vs-aria-hidden", "comparison", "HTML hidden versus aria-hidden: rendering and accessibility are different scopes",
    "hidden removes an element from normal rendering; aria-hidden only adjusts accessibility-tree exposure.",
    "The decorative separator is visible but has no useful spoken meaning, so aria-hidden can keep it out of accessibility output. The future content is unavailable to everyone and uses hidden. Neither attribute is an access-control mechanism; both nodes remain in the delivered document.",
    '''<p>Receipt R-47 <span aria-hidden="true">|</span> Pending review</p>
<section hidden>
  <h2>Future export options</h2>
  <p>These controls are not ready.</p>
</section>''',
    "Never put a focusable control under aria-hidden=true while leaving it keyboard reachable. For a whole inactive interactive region, use an appropriate state design such as hidden or inert and test the transition.",
    "The attributes add no network cost, but a mismatch between visual state, keyboard focus, and accessibility-tree state creates a hard-to-debug user failure.",
    ["Do not use aria-hidden to visually hide text.", "Do not hide a focused descendant from the accessibility tree.", "Neither attribute keeps secrets out of page source."],
    ["html/hidden-and-inert", "html/focus-and-native-controls", "html/character-references"])

add("table-vs-layout", "comparison", "HTML data table versus layout container: preserve relationships, not columns",
    "A data table is for values related by headers; layout containers group content for styling or document structure.",
    "The receipt queue has columns whose headers explain each cell, so it belongs in a table. The action links below are navigation, not another table row created to align them. CSS controls their visual layout without changing the data relationship.",
    '''<table>
  <caption>Receipts awaiting review</caption>
  <thead><tr><th scope="col">ID</th><th scope="col">Amount</th></tr></thead>
  <tbody><tr><th scope="row">R-47</th><td>73 credits</td></tr></tbody>
</table>
<nav aria-label="Receipt actions">
  <a href="/receipts/R-47">Open R-47</a>
</nav>''',
    "A CSS grid can present data visually, but it will not supply native table header associations. Conversely, a table used to place a menu and footer creates false row and column relationships.",
    "Tables add DOM elements proportional to rows and columns. Large datasets need pagination or summarization; layout containers need CSS but should follow a meaningful source order.",
    ["Do not use table markup to position an entire page.", "Do not replace a real data table with visually aligned divs without an equivalent relationship model.", "Use a caption and headers for meaningful data."],
    ["html/data-tables", "html/landmarks", "css/box-model-and-layout"])

add("receipt-review-form-project", "project", "HTML receipt review form project: one native flow with clear server boundaries",
    "A review form combines labeled controls, grouped choices, a note, and a submit action into one accessible task.",
    "The reviewer selects approve or hold and may leave a short note. The receipt ID is shown in the heading and carried as a hidden request value. Every submitted value remains untrusted: the server must resolve the record, authorize this reviewer, reject stale state, and protect the POST action against request forgery.",
    '''<main>
  <h1>Review receipt R-47</h1>
  <form action="/receipts/review" method="post">
    <input type="hidden" name="receipt_id" value="R-47">
    <fieldset>
      <legend>Decision</legend>
      <label><input type="radio" name="decision" value="approve" required> Approve</label>
      <label><input type="radio" name="decision" value="hold"> Hold</label>
    </fieldset>
    <label for="review-note">Reason</label>
    <textarea id="review-note" name="reason" maxlength="240"></textarea>
    <button type="submit">Save decision</button>
  </form>
</main>''',
    "This is a front-end document, not a running approval service. A full implementation also needs a server endpoint, data persistence, an error response, and tests for repeated submission and changed receipt status.",
    "The static HTML is small and works without a client bundle. The service side owns the expensive part: validation, transaction isolation, audit history, and failure recovery.",
    ["Do not trust the hidden receipt ID as authorization.", "Do not leave a required decision without a group legend.", "A successful native submission still needs a confirmation or error page."],
    ["html/forms-get-post", "html/radio-checkbox", "html/form-labels", "html/form-validation"])

add("receipt-index-project", "project", "HTML receipt index project: landmarks, links, tables, and a bounded image",
    "A useful index page combines a named document, one main task, direct record links, and tabular status data.",
    "The page can render meaningful information before styling or scripting. A small logo has an empty alt because the adjacent text already names the site. A table presents actual records; each ID is a link whose target must be served by the application.",
    '''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Receipt index | AI Trove</title></head>
<body>
  <a href="#content">Skip to receipts</a>
  <header><p><img src="/media/aitrove-mark.svg" alt="" width="24" height="24"> AI Trove</p></header>
  <main id="content">
    <h1>Receipt index</h1>
    <table>
      <caption>Current review queue</caption>
      <thead><tr><th scope="col">Receipt</th><th scope="col">State</th></tr></thead>
      <tbody><tr><th scope="row"><a href="/receipts/R-47">R-47</a></th><td>Pending</td></tr></tbody>
    </table>
  </main>
</body>
</html>''',
    "The logo and record route are owned assets/endpoints that must exist. Add responsive CSS when shipping the complete page; the viewport declaration cannot repair a fixed-width design by itself.",
    "The HTML is inexpensive for a short queue. For thousands of records, paginate on the server rather than pushing a huge table into one response.",
    ["Do not treat a broken route as a valid example of navigation.", "Keep the linked image's text alternative empty only because site text is adjacent.", "Do not let a long table substitute for filtering and pagination."],
    ["html/document-skeleton", "html/landmarks", "html/data-tables", "html/image-alt"])


section_info = {
    "core": ("html/html-tutorial", "html", "HTML Tutorial", "Document setup, text, links, and element selection."),
    "semantics": ("html/html-tutorial/semantics", "html-semantics", "HTML Semantics", "Landmarks, sections, figures, data tables, and machine-readable values."),
    "forms": ("html/html-tutorial/forms", "html-forms", "HTML Forms", "Submission contracts, field names, labels, choices, validation, and uploads."),
    "media": ("html/html-tutorial/media", "html-media", "HTML Media", "Image alternatives, responsive assets, timed media, frames, and script loading."),
    "accessibility": ("html/html-tutorial/accessibility", "html-accessibility", "HTML Accessibility", "Keyboard focus, hidden states, disclosures, and language direction."),
    "comparison": ("html/html-tutorial/comparison", "html-comparison", "HTML Comparisons", "Choose elements by behavior and meaning."),
    "project": ("html/html-tutorial/project", "html-project", "HTML Projects", "Small pages with explicit back-end and asset boundaries."),
    "quizzes": ("html/quizzes", "html-quizzes", "HTML Quizzes", "Check the document, form, media, and accessibility contracts."),
}
titles = {row["path"]: row["title"] for row in rows}
titles.update({"html/" + item["slug"]: item["title"] for item in lessons})
for item in lessons:
    assert "html/" + item["slug"] not in by_path
    assert all(target in titles for target in item["links"]), item["slug"]


def lesson_body(item):
    body = "<p>" + html.escape(item["definition"]) + "</p>"
    body += "<h2>Use it for a real task</h2><p>" + html.escape(item["scenario"]) + "</p>"
    body += '<pre><code class="language-html">' + html.escape(item["code"], quote=False) + "</code></pre>"
    body += "<h2>What the markup guarantees</h2><p>" + html.escape(item["consequence"]) + "</p>"
    body += "<h2>Cost and limits</h2><p>" + html.escape(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(
        "<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>"
        for target in item["links"]) + "</ul>"
    return body


for index, item in enumerate(lessons):
    path = "html/" + item["slug"]
    section_path, subject, _, _ = section_info[item["section"]]
    row = copy.deepcopy(by_path["html/html-tags-a-to-z-list"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["definition"], body=lesson_body(item),
               category="Web Development", subject=subject, difficulty="Intermediate",
               tags=["html", item["section"]], sort_order=1000 + index,
               published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "html/html-tutorial", "section_path": section_path,
                   "content_format": "html", "kind": "project" if item["section"] == "project" else "tutorial",
                   "reading_minutes": 6, "author_path": "authors/aitrove-editorial",
                   "related": [{"path": target, "title": titles[target]} for target in item["links"]],
                   "seo_ready": True}
    rows.append(row)
    by_path[path] = row


reference = by_path["html/html-tags-a-to-z-list"]
reference["title"] = "HTML Elements Reference: select elements by content contract"
reference["summary"] = "Find common HTML elements by role and check what their attributes actually change."
titles[reference["path"]] = reference["title"]
reference["body"] = (
    "<p>HTML elements identify the structure, interaction, and embedded resources in a document. Choose an element for what the content does; CSS decides how it looks.</p>"
    "<h2>Document and landmarks</h2><ul>"
    "<li>html carries the page language. head holds metadata; body holds rendered content.</li>"
    "<li>header, nav, main, aside, and footer identify major regions. Give multiple nav regions distinct names.</li>"
    "<li>article stands on its own; section groups related content under a heading.</li></ul>"
    "<h2>Text and data</h2><ul>"
    "<li>h1 through h6 express heading levels; p groups prose. ol and ul express sequence or a collection.</li>"
    "<li>dl pairs terms with descriptions. figure and figcaption keep a self-contained asset with its caption.</li>"
    "<li>table, caption, th, tr, and td express a data grid. time and data carry machine-readable values.</li></ul>"
    "<h2>Navigation, controls, and media</h2><ul>"
    "<li>a with href navigates. button acts or submits. form owns named controls such as input, select, and textarea.</li>"
    "<li>label names a control; fieldset and legend name a group. details and summary expose a disclosure.</li>"
    "<li>img carries an alt decision. picture offers source alternatives. video and track carry timed media and captions; iframe embeds another document.</li></ul>"
    '<h2>Small complete case</h2><pre><code class="language-html">'
    + html.escape('''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Receipt status</title></head>
<body>
  <main>
    <h1>Receipt R-47</h1>
    <p>Status: <data value="pending">Pending review</data></p>
    <a href="/receipts">Return to receipt index</a>
  </main>
</body>
</html>''', quote=False) + "</code></pre>"
    "<h2>Cost and limits</h2><p>Native semantics require no framework. The cost appears when a visual component is built from generic containers and then needs manually recreated keyboard, naming, and form behavior. This reference groups common elements; it is not an alphabetic inventory of every element or attribute.</p>"
    "<h3>Common Mistakes</h3><ul><li>Choose a heading for hierarchy, not font size.</li><li>Use a button for a local action and an anchor for navigation.</li><li>Do not use a table to position unrelated page regions.</li></ul>"
    '<h2>Read next</h2><p><a href="/html/document-skeleton">Document setup</a>, '
    '<a href="/html/landmarks">landmarks</a>, <a href="/html/forms-get-post">forms</a>, '
    '<a href="/html/image-alt">images</a>, and <a href="/html/data-tables">tables</a>.</p>'
)
reference["data"].update(content_format="html", seo_ready=True,
                         related=[{"path": path, "title": titles[path]} for path in
                                  ["html/document-skeleton", "html/landmarks", "html/forms-get-post", "html/image-alt"]])
reference["updated_at"] = stamp

button = by_path["html/button-tag-vs-input-typebutton-attribute"]
button["title"] = "HTML button versus input type=button: content and default action"
button["summary"] = "Both create buttons, but button can contain phrasing content and must declare its form behavior deliberately."
titles[button["path"]] = button["title"]
button["body"] = (
    "<p>A button element can contain text and other phrasing content; an input type=button gets its label from value. Neither label alone gives a control a useful action.</p>"
    "<h2>Choose by content and ownership</h2><p>A receipt review control needs a short icon and visible text. button can contain both. Inside a form, declare type=button for a local interface action; the default missing type can submit the form. For actual submission, use type=submit and let the server handle the request.</p>"
    '<pre><code class="language-html">' + html.escape('''<form action="/receipts/review" method="post">
  <button type="button" aria-label="Show receipt help">?</button>
  <input type="button" value="Preview receipt">
  <button type="submit">Save review</button>
</form>''', quote=False) + "</code></pre>"
    "<h2>Behavior boundary</h2><p>The two non-submit controls need application behavior before they do anything useful. The submit button invokes the form endpoint. The question-mark button needs a tested accessible name and a working help panel; do not publish a dead control just because its markup looks right.</p>"
    "<h2>Cost and limits</h2><p>Both elements are native keyboard controls. An input button is compact for a text-only label, while button handles richer phrasing. Avoid nesting another interactive control inside button.</p>"
    "<h3>Common Mistakes</h3><ul><li>Omitting type inside a form can submit unexpectedly.</li><li>An icon-only button needs an accessible name.</li><li>type=button does not create behavior by itself.</li></ul>"
    '<h2>Read next</h2><p><a href="/html/link-vs-button">Navigation versus action</a>, '
    '<a href="/html/forms-get-post">form methods</a>, and <a href="/html/focus-and-native-controls">focus order</a>.</p>'
)
button["data"].update(content_format="html", seo_ready=True,
                      related=[{"path": path, "title": titles[path]} for path in
                               ["html/link-vs-button", "html/forms-get-post", "html/focus-and-native-controls"]])
button["updated_at"] = stamp

projects = by_path["html/web-development-projects"]
projects["title"] = "HTML projects: build a receipt index and a review form"
projects["summary"] = "Two small pages exercise navigation, data tables, labels, decisions, and server boundaries."
titles[projects["path"]] = projects["title"]
projects["body"] = (
    "<p>HTML projects should prove that structure and controls still make sense before CSS and JavaScript are added. Build two pages: a receipt index for reading and a review form for a state-changing decision.</p>"
    '<h2>Index first</h2><p>Start with <a href="/html/receipt-index-project">the receipt index</a>. '
    "Give the document a title, one main region, a captioned data table, and real links for each record. Check that the source order matches the reading order at narrow widths.</p>"
    '<h2>Then the decision</h2><p>Build <a href="/html/receipt-review-form-project">the review form</a> '
    "with a fieldset, explicit values, a visible note label, and a submit button. Treat its POST endpoint as a separate implementation requirement. The HTML does not approve a receipt on its own.</p>"
    '<pre><code class="language-html">' + html.escape('''<nav aria-label="Practice pages">
  <a href="/receipts">Open the receipt index</a>
  <a href="/receipts/R-47/review">Review receipt R-47</a>
</nav>''', quote=False) + "</code></pre>"
    "<h2>Cost and limits</h2><p>The static documents are small. A production version needs routes, persistence, permission checks, a request-forgery defense, input validation, error handling, and tests. Add styling through the separate CSS curriculum after the source order works.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not present a form as a finished service without its endpoint.</li><li>Do not use a hidden receipt ID as authorization.</li><li>Test links and labels before polishing visual layout.</li></ul>"
    '<h2>Connected lessons</h2><p><a href="/html/landmarks">Landmarks</a>, '
    '<a href="/html/data-tables">data tables</a>, <a href="/html/form-labels">labels</a>, '
    '<a href="/css/responsive-layout">responsive CSS</a>.</p>'
)
projects["data"].update(content_format="html", seo_ready=True,
                        related=[{"path": path, "title": titles[path]} for path in
                                 ["html/receipt-index-project", "html/receipt-review-form-project", "css/responsive-layout"]])
projects["updated_at"] = stamp


for section, (path, subject, title, description) in section_info.items():
    if path not in by_path:
        template = copy.deepcopy(by_path["html/html-tutorial/comparison"])
        template.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
                        path=path, title=title, summary=description,
                        category="Web Development", subject=subject, tags=["html", section],
                        sort_order=10 + len(rows), published_at=stamp, created_at=stamp,
                        updated_at=stamp)
        template["data"] = {"subject_root": "html/html-tutorial", "section_path": path,
                            "content_format": "html", "author_path": "authors/aitrove-editorial",
                            "seo_ready": True, "modules": []}
        rows.append(template)
        by_path[path] = template

modules = {section: ["html/" + item["slug"] for item in lessons if item["section"] == section]
           for section in section_info}
modules["core"].insert(0, reference["path"])
modules["comparison"].insert(0, button["path"])
modules["project"].insert(0, projects["path"])

for section, (path, subject, title, description) in section_info.items():
    hub = by_path[path]
    hub["summary"] = description
    hub["body"] = "<p>" + html.escape(description) + "</p>"
    hub["data"].update(subject_root="html/html-tutorial", section_path=path,
                       content_format="html", seo_ready=True,
                       author_path="authors/aitrove-editorial")
    if section == "core":
        hub["data"]["modules"] = [
            {"title": "Build a document", "summary": "Source order, metadata, and headings.",
             "lessons": modules["core"][:4]},
            {"title": "Text and navigation", "summary": "Lists, links, and text escaping.",
             "lessons": modules["core"][4:]},
        ]
    elif section != "quizzes":
        hub["data"]["modules"] = [{"title": title, "summary": description, "lessons": modules[section]}]
    hub["body"] += "<h2>Learning path</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>"
        for target in modules[section]) + "</ul>"
    if section != "core":
        hub["body"] += '<p><a href="/html/html-tutorial">Return to the HTML tutorial</a>.</p>'
    hub["body"] += "<h3>Common Mistakes</h3><p>Read the behavior boundary on each page before treating an isolated markup sample as a complete application.</p>"
    hub["updated_at"] = stamp

tabs = [{"title": title, "path": path} for path, _, title, _ in section_info.values()]
by_path["html/html-tutorial"]["data"]["resource_tabs"] = tabs
for section, (path, _, _, _) in section_info.items():
    if section == "core":
        continue
    by_path["html/html-tutorial"]["body"] += '<p><a href="/' + path + '">Explore ' + html.escape(section_info[section][2]) + "</a>.</p>"

for item in lessons:
    target = "html/" + item["slug"]
    for source in item["links"]:
        if source.startswith("html/") and source in by_path and by_path[source]["type"] == "article":
            by_path[source]["body"] += '<p><a href="/' + target + '">Related: ' + html.escape(item["title"]) + "</a>.</p>"
            by_path[source]["updated_at"] = stamp


quiz_sets = [
    ("quizzes/html-document-structure", "HTML document structure quiz", "core",
     [
         ("Which element identifies the primary page content?", "main", "header", "aside", "main owns the primary task region."),
         ("What names a browser tab and history entry?", "title", "h1 only", "meta description", "The title element names the document outside its visible page."),
         ("What does an anchor need to be a navigation link?", "href", "role=button", "tabindex only", "The href supplies a destination and native link behavior."),
         ("What should identify a simple data table?", "caption and header cells", "only CSS columns", "a footer", "A caption and th cells give values their relationships."),
         ("When is article appropriate?", "When content stands on its own", "For every styled card", "Only in a page footer", "Article marks self-contained content."),
         ("What does an empty alt mean for a decorative icon?", "It adds no separate information", "The file is broken", "The image is secret", "Empty alt avoids repeating adjacent equivalent text."),
         ("What happens to a link with a duplicate fragment id target?", "The target becomes ambiguous", "Both targets open", "The browser rejects HTML", "IDs should be unique within one document."),
         ("Which list fits a process whose order matters?", "ol", "ul only", "dl only", "Ordered lists retain the sequence relationship."),
         ("What does the viewport meta declaration do by itself?", "Sets viewport interpretation", "Makes all widths responsive", "Changes heading levels", "Responsive layout still requires suitable CSS and content sizing."),
         ("How should untrusted text be inserted into HTML?", "Through context-aware escaping", "By joining raw strings", "By URL encoding only", "Text and attribute contexts need correct output handling."),
         ("What does figure group?", "Self-contained content and an optional caption", "Only photographs", "A form's controls", "Figure can connect a chart or other asset with its caption."),
         ("What does a time datetime value need to match?", "Its visible meaning", "The CSS color", "The file path", "Machine and human values should not conflict."),
     ]),
    ("quizzes/html-forms-and-accessibility", "HTML forms and accessibility quiz", "forms",
     [
         ("Which form method fits a read-only search?", "GET", "POST only", "DELETE in HTML", "A retrieval query can be represented in the URL."),
         ("What names a field in ordinary form submission?", "name", "id alone", "class", "Successful controls contribute their name and value."),
         ("Does a disabled control normally submit its value?", "No", "Yes", "Only on POST", "Disabled controls are excluded from normal form entries."),
         ("What links an explicit label to a control?", "for matching a unique id", "Matching class names", "Adjacent CSS", "The label's for points to a control id."),
         ("Does required replace server validation?", "No", "Yes", "Only for email", "Clients can bypass or change browser markup."),
         ("What does an unchecked checkbox normally contribute?", "No entry", "A false string", "A zero integer", "The endpoint needs a defined missing-value rule."),
         ("Which encoding is used for a file upload form?", "multipart/form-data", "text/plain always", "application/json automatically", "A file control needs multipart submission to carry the file as intended."),
         ("Is accept on a file input content validation?", "No", "Yes", "Only for PDF", "The server must inspect and bound received bytes."),
         ("What does aria-required add to a custom control?", "Accessibility semantics", "Native constraint validation", "Automatic server validation", "ARIA communicates state but does not implement behavior."),
         ("What does a full sandboxed iframe need for its purpose?", "A descriptive title", "A hidden password", "A table caption", "A frame title identifies its embedded content."),
         ("Does dialog open alone create a modal dialog?", "No", "Yes", "Only on mobile", "Modal behavior requires the modal opening API and focus ownership."),
         ("Which action belongs in a native button?", "Submitting a review", "Navigating to a receipt route", "Linking to a fragment", "An action uses a button; navigation uses an anchor."),
     ]),
]

quiz_hub = by_path["html/quizzes"]
quiz_hub["data"]["modules"] = []
for index, (path, title, section, raw_questions) in enumerate(quiz_sets):
    template = copy.deepcopy(by_path["quizzes/python-stdlib-state-contracts"])
    linked_paths = modules[section][:6]
    body = "<p>Check the HTML contracts before adapting a sample into an application.</p><h2>Review the lessons</h2><ul>"
    body += "".join('<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>" for target in linked_paths)
    body += "</ul><h3>Common Mistakes</h3><p>Markup examples do not supply missing routes, assets, persistence, or authorization checks.</p>"
    template.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
                    path=path, title=title, summary="Twelve explained checks on HTML behavior and failure boundaries.",
                    body=body, category="Web Development", subject="html-quizzes",
                    tags=["html", "quiz"], sort_order=3000 + index,
                    published_at=stamp, created_at=stamp, updated_at=stamp)
    template["data"] = {"subject_root": "html/html-tutorial", "section_path": "html/quizzes",
                        "content_format": "html", "author_path": "authors/aitrove-editorial",
                        "seo_ready": True, "duration_minutes": 12,
                        "related": [{"path": target, "title": titles[target]} for target in linked_paths],
                        "questions": []}
    for question_index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(raw_questions):
        options = [correct, wrong_a, wrong_b]
        options = options[question_index % 3:] + options[:question_index % 3]
        template["data"]["questions"].append({"prompt": prompt, "options": options,
                                                 "answer": options.index(correct), "explanation": explanation})
    rows.append(template)
    by_path[path] = template
    titles[path] = title
    quiz_hub["data"]["modules"].append({"title": title, "summary": "Twelve questions with explanations.",
                                         "lessons": [path]})
    by_path["html/html-tutorial"]["body"] += '<p><a href="/' + path + '">Check ' + html.escape(title) + "</a>.</p>"

quiz_hub["body"] = (
    "<p>Use these checks after working through the HTML lessons. Each answer explains the browser contract and the application boundary.</p>"
    "<h2>HTML self checks</h2><ul>"
    + "".join('<li><a href="/' + path + '">' + html.escape(title) + "</a></li>"
              for path, title, _, _ in quiz_sets)
    + "</ul><h3>Common Mistakes</h3><p>A correct HTML answer does not establish that a route, asset, or server handler exists in the running site.</p>"
)

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("HTML lessons", len(lessons), "hubs", len(section_info), "quizzes", len(quiz_sets))

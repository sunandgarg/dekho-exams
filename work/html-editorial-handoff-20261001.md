# HTML editorial handoff — 2026-10-01

The public HTML lesson bodies use original prose and examples. They contain no research URLs. The five user-preferred pages were reviewed; they cover Java and Java `LinkedList`, so they did not govern HTML claims or examples.

## Research checked for the latest batches

- HTML Standard, form infrastructure: `https://html.spec.whatwg.org/multipage/form-control-infrastructure.html`
- HTML Standard, form elements and buttons: `https://html.spec.whatwg.org/multipage/form-elements.html`
- HTML Standard, file input and `accept`: `https://html.spec.whatwg.org/multipage/input.html`
- HTML Standard, images and decoding: `https://html.spec.whatwg.org/multipage/images.html`
- HTML Standard, interaction and autofocus: `https://html.spec.whatwg.org/multipage/interaction.html`
- HTML Standard, link elements and stylesheet media: `https://html.spec.whatwg.org/multipage/semantics.html`
- W3C WAI, form notifications: `https://www.w3.org/WAI/tutorials/forms/notifications/`
- W3C WAI, functional images: `https://www.w3.org/WAI/tutorials/images/functional/`
- W3C WAI, table captions and summaries: `https://www.w3.org/WAI/tutorials/tables/caption-summary/`
- W3C WAI, media transcripts: `https://www.w3.org/WAI/media/av/transcripts/`
- W3C WAI, form control labels: `https://www.w3.org/WAI/tutorials/forms/labels/`
- HTML Standard, input states and constraints: `https://html.spec.whatwg.org/multipage/input.html`
- HTML Standard, document metadata: `https://html.spec.whatwg.org/multipage/semantics.html`
- HTML Standard, translate attribute: `https://html.spec.whatwg.org/multipage/dom.html`
- HTML Standard, preformatted text: `https://html.spec.whatwg.org/multipage/grouping-content.html`
- HTML Standard, element index: `https://html.spec.whatwg.org/dev/indices.html`
- HTML Standard, inline text semantics: `https://html.spec.whatwg.org/multipage/text-level-semantics.html`
- HTML Standard, modulepreload link type: `https://html.spec.whatwg.org/multipage/links.html`
- HTML Standard, popover states and dismissal: `https://html.spec.whatwg.org/multipage/popover.html`
- HTML Standard, video and playsinline: `https://html.spec.whatwg.org/multipage/media.html`
- W3C HTML Media Capture, capture attribute: `https://www.w3.org/TR/html-media-capture/`
- HTML Standard, ordered lists: `https://html.spec.whatwg.org/multipage/grouping-content.html`
- HTML Standard, button commands: `https://html.spec.whatwg.org/multipage/form-elements.html`
- HTML Standard, dialog dismissal: `https://html.spec.whatwg.org/multipage/interactive-elements.html`
- HTML Standard, iframe referrer policy: `https://html.spec.whatwg.org/multipage/iframe-embed-object.html`
- W3C Subresource Integrity: `https://www.w3.org/TR/sri/`

## Current scope and checks

The fixture curriculum has 156 HTML articles, 9 hubs, 7 quiz banks, 84 quiz questions, and 1080 resolved body links. Forty-nine HTML articles contain 109 CSS body links, connecting document patterns to styling decisions. The newest links connect custom-element state, disclosure content, text targets, navigation, scripting, modal dialogs, and video presentation to focused CSS decisions; preceding links cover shadow roots, slots, validation, print, direction, images, media, and form states. The local content validator found no orphan page and checked one HTML sample per article. This day's lessons include `button-type-default`, `dialog-form-method`, `file-accept-hint`, `password-autocomplete-tokens`, `print-stylesheet-media`, `image-decoding-hint`, `textarea-wrap-submission`, `aria-invalid-errors`, `draft-formnovalidate`, `submitter-name-value`, `autofocus-dialog`, `linked-image-alt`, `table-caption-and-summary`, `video-descriptive-transcript`, `audio-transcript`, `telephone-input`, and `image-submit-button`. The project index links seven complete project lessons, including `incident-evidence-project` and `server-error-response-project`. Later articles cover numeric step boundaries, multiple-file selection, color-scheme metadata, translation boundaries, preformatted code, a search form contract, relevant-text highlighting, meaningful breaks, and input-output notation. Nine subsequent lessons distinguish file-capture hints, inline video playback, module preloading, manual popover dismissal, ordered-list numbering, dialog commands, dialog close policy, iframe referrer policy, and subresource integrity. The integrity example is checked against the shipped stylesheet bytes. The element reference covers 107 built-in element entries across eight purpose-based groups, while keeping its existing route. The core, forms, semantics, media, accessibility, advanced, comparison, and quiz hubs now group lessons by task; misplaced recent entries have been corrected. `html-production-review` and `html-browser-contracts` each test 12 applied decisions.

`scripts/export-html-for-wordpress.py` writes `work/aitrove-html-import-drafts.json`. It contains the 172 HTML curriculum entries plus the editorial author, all as drafts with `seo_ready=false` for review. The WordPress import is idempotent by path, but this file has not been imported. After review, publish entries and set `seo_ready=true` deliberately. Some HTML lessons link to other subjects and illustrative application routes; an HTML-only import assumes the rest of the approved site corpus and real application endpoints are in place. Do not publish illustrative code routes as working features.

## Remaining work

- Deploy the committed build to Cloudflare when Wrangler authentication is restored. On 2026-10-01, `wrangler whoami` reported an expired token in the noninteractive environment, and an HTTP HEAD request for the new `html/file-capture-hint` route returned 404. The GitHub push does not by itself prove the Pages site updated. `WORDPRESS_URL` and the checked WordPress and Cloudflare credentials are absent from this environment; the HTML fixture additions need an editorial WordPress import and publication before a CMS-backed frontend will serve them. A local Vite browser smoke test was attempted but its configured inspector port 9230 was already in use, so this pass relies on the content validator and successful production build rather than a new browser observation.
- Run a live browser and assistive-technology review for dialog focus, error announcements, print preview, form keyboard submission, and mobile file selection. The static checker cannot establish those outcomes.
- Further HTML coverage has no finite completion percentage. Add another lesson or end-to-end form only when it introduces a distinct behavior or testable decision; avoid near-duplicate pages built solely to raise the count.
- The requested 80% humanized score has no trustworthy verification in this repository; do not report it as achieved.

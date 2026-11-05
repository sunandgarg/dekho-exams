"""Add broad Web Development topic tracks with useful starter lessons."""

import copy
import datetime
import html
import json
import re
import subprocess
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
assert "web-tech/web-technology" in by_path
stamp = datetime.datetime.now(datetime.UTC).isoformat()

themes = [
    dict(path="web-tech/frontend-application-architecture", title="Frontend Application Architecture",
         summary="Organize page state, navigation, rendering, and locale behavior without losing the HTML baseline.",
         overview="A frontend architecture decides what the server renders, what the browser owns, and which state must survive navigation. These decisions affect accessibility, load cost, failure handling, and the team's ability to change one screen without breaking another.",
         bridge=["web-tech/dom-events-progressive-enhancement", "html/html-tutorial", "css/css-tutorial"]),
    dict(path="web-tech/backend-api-systems", title="Backend and API Systems",
         summary="Shape read and write endpoints for growing collections and unreliable networks.",
         overview="An API is a contract across a network boundary. Pagination, retries, background work, and abuse limits must be explicit because the client cannot know whether a slow or interrupted request has already changed server state.",
         bridge=["web-tech/http-request-response-contract", "web-tech/form-server-validation", "web-tech/route-parameters-and-error-responses"]),
    dict(path="web-tech/data-persistence", title="Data Persistence",
         summary="Model records, preserve invariants under concurrent writes, and change schemas safely.",
         overview="Durable data outlives an individual request and often outlives several application versions. Tables, constraints, transactions, indexes, and migration stages should express the behavior the service promises to users.",
         bridge=["web-tech/form-server-validation", "web-tech/record-level-authorization", "web-tech/cache-etag-revalidation"]),
    dict(path="web-tech/media-and-live-updates", title="Media and Live Updates",
         summary="Accept files, serve useful image sizes, and deliver ordered changes to active pages.",
         overview="Media and live updates cross different resource limits. A file upload needs storage and type checks; an image needs a delivery budget; a live stream needs reconnection and ordering rules. Treat each as a specific contract rather than a generic byte pipe.",
         bridge=["web-tech/browser-parse-load-and-render", "web-tech/fetch-status-and-abort", "html/responsive-images"]),
    dict(path="web-tech/offline-and-device-capabilities", title="Offline and Device Capabilities",
         summary="Cache a useful shell, keep local drafts, and reconcile changes after reconnecting.",
         overview="Offline features are promises about what still works without a network. A service worker can serve a known shell, local storage can hold drafts, and a sync rule decides what happens if the server changed meanwhile. Installation is optional and never substitutes for a usable website.",
         bridge=["web-tech/browser-storage-boundary", "web-tech/fetch-status-and-abort", "web-tech/cache-etag-revalidation"]),
    dict(path="web-tech/deployment-and-scale", title="Deployment and Scale",
         summary="Configure releases, gate changes, share state, and prove recovery from data loss.",
         overview="Production reliability includes configuration, repeatable checks, shared state, and tested recovery. A successful build is only one gate; deployed behavior must be observed, and a backup is useful only when a restore has been rehearsed.",
         bridge=["web-tech/release-smoke-and-rollback", "web-tech/observability-and-recovery", "devops/devops-tutorial"]),
    dict(path="web-tech/content-discovery-and-structure", title="Content Discovery and Structure",
         summary="Give public pages stable identities, navigable paths, and machine-readable meaning.",
         overview="A public page needs a clear title and content, a stable canonical location, and links that make it reachable. Discovery metadata can clarify the page's role, but it cannot replace useful text or correct server responses.",
         bridge=["web-tech/browser-parse-load-and-render", "html/document-skeleton", "web-tech/release-smoke-and-rollback"]),
]

topics = []

topics.extend([
    dict(path="web-tech/component-boundaries-and-state", theme=themes[0]["path"], title="Component Boundaries and State Ownership",
         summary="Keep source records, temporary input, and derived display values in distinct places.",
         definition="A component boundary is useful when it gives one part of the interface a clear input and output contract. The server owns the case record; the page owns the current fetched copy; a form owns its unfinished note. A count derived from that record should be calculated rather than copied into a second mutable variable. This keeps two views from disagreeing after an update. State shared across several pages needs a deliberate owner, not a chain of callbacks that silently edits distant controls.",
         case="An inspection page shows case 47, its notes, and a note editor. The editor keeps draft text while the page keeps the saved notes returned by the service. Submitting the form does not add an optimistic note to the official list until the write contract confirms it. If the write fails, the draft remains. If a second case opens, the editor resets to that case rather than retaining the first case's draft. A small rendering function can take a saved record and an existing target node without reaching into unrelated widgets.",
         cost="Rendering a list of N notes requires O(N) DOM work if the whole list is rebuilt. Updating one changed item can be smaller, but only if identity and ordering stay correct. Duplicating derived values adds synchronization cost and more failure paths. A component layer also has a maintenance cost; split a screen when its state and responsibilities justify it, not merely because a file reached a line count. Measure rerenders in the actual UI before adding memoization or a global store.",
         mistakes=["Do not store the same derived count in two mutable places.", "Do not let an unsaved draft appear as a committed record.", "Do not let one case editor retain another case's draft."],
         language="javascript", code='''function renderSavedNotes(savedNotes, notesList) {
  const fragment = document.createDocumentFragment();
  for (const note of savedNotes) {
    const item = document.createElement("li");
    item.textContent = note.text;
    fragment.append(item);
  }
  notesList.replaceChildren(fragment);
}'''),
    dict(path="web-tech/browser-routing-and-history", theme=themes[0]["path"], title="Browser Routing and History State",
         summary="Keep client navigation aligned with a route the server can open directly.",
         definition="A client router may intercept links and update the visible view without reloading the document. It still needs a server route for direct visits, refreshes, and shared links. The History API changes the current history entry or pushes a new one, but it does not fetch content or make the server understand that path. A popstate handler must restore the view when the user moves backward or forward. Preserve actual anchors so keyboard interaction, open-in-new-tab, and script-free navigation remain available.",
         case="An analyst moves from the case list to case 47 and then presses Back. A client enhancement can fetch case 47, push its path after a successful render, and restore the list view on popstate. If the fetch fails, leave the original link navigation available. Opening the copied case path in a fresh tab must return the case page from the server. A route that works only after clicking from the homepage is incomplete, even if the in-app transition looks fast.",
         cost="A history mutation is O(1) local work; rendering a fetched view costs O(B) for response size B and any DOM updates. Caching route data can save requests but needs invalidation after writes. Holding every previous page tree in memory can grow with navigation length; storing only small route state avoids that pressure. Test direct, refresh, Back, Forward, and failed-fetch paths. The code below shows a conservative path: if the enhanced load fails, the browser follows the original anchor.",
         mistakes=["Do not replace real links with click-only spans.", "Do not push a path that the server cannot serve on refresh.", "Do not forget popstate after adding pushState."],
         language="javascript", code='''const caseLink = document.querySelector("#open-case-47");
const casePanel = document.querySelector("#case-panel");
caseLink.addEventListener("click", async (event) => {
  if (event.button !== 0 || event.metaKey || event.ctrlKey) return;
  event.preventDefault();
  try {
    const response = await fetch(`/api${caseLink.pathname}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const caseRecord = await response.json();
    casePanel.textContent = `${caseRecord.title}: ${caseRecord.status}`;
    history.pushState({ caseId: 47 }, "", caseLink.pathname);
  } catch { location.assign(caseLink.href); }
});
addEventListener("popstate", () => location.reload());'''),
    dict(path="web-tech/server-rendered-static-and-client-rendered-pages", theme=themes[0]["path"], title="Static, Server-Rendered, and Client-Rendered Pages",
         summary="Choose a rendering boundary from data freshness, interaction, and failure needs.",
         definition="A static page is built before a request and can be cached widely. A server-rendered page assembles HTML for a request, possibly using a session and current record. A client-rendered page sends a shell and asks browser code to fetch the meaningful content later. These modes can coexist on one site. The right choice depends on whether the first response must contain useful text, how often data changes, whether the view is private, and how much browser work the interaction requires. Avoid making a tiny read-only page wait for a large client bundle without a reason.",
         case="A public guide to inspection terms changes weekly and works well as static HTML. A private case page needs current permission checks and can be rendered on the server per request. A live status widget on that page may fetch updates after the initial HTML arrives. This combination keeps the record readable when enhancement fails while still supporting fresh status. Caching a private server-rendered page as though it were public would leak data; rendering every public guide from a database on each visit wastes work without adding value.",
         cost="Static delivery can avoid per-request template and database work, but rebuilding many pages after one edit has a cost. Server rendering adds request-time CPU and data lookup; browser rendering adds script transfer, parsing, execution, and a later data request before text appears. Compare real first-load and interaction traces, not framework slogans. The example below represents the server boundary: escape record text before inserting it into HTML, then send a complete page that does not require client code to reveal its title.",
         mistakes=["Do not put private data in a shared public cache.", "Do not make essential text depend solely on a delayed client fetch.", "Do not force one rendering mode onto every route."],
         language="javascript", code='''function escapeText(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}
function renderCasePage(caseRecord) {
  return `<main><h1>${escapeText(caseRecord.title)}</h1>` +
    `<p>Status: ${escapeText(caseRecord.status)}</p></main>`;
}'''),
    dict(path="web-tech/locale-and-time-zone-boundaries", theme=themes[0]["path"], title="Locale and Time-Zone Boundaries",
         summary="Store an unambiguous instant and format it for the reader at the edge.",
         definition="A stored timestamp should identify an instant without depending on the machine's local clock setting. The page can then format that instant for the reader's locale and chosen time zone. A locale changes number and date presentation; a time zone changes the displayed wall time. Neither should silently change the stored event. User-entered local times are harder: a daylight-saving transition can make a wall time ambiguous or nonexistent, so a scheduling form needs an explicit zone and an ambiguity policy. Keep the original instant or zone with the record that requires it.",
         case="A service inspection happened at a recorded UTC instant. One reviewer sees the event in Delhi local time; another sees it in London local time. Both refer to the same event ID and stored timestamp. Sorting should use the underlying instant, not formatted labels such as '4/10/26'. A saved appointment for a future local time may need the intended zone preserved because future offsets can change. The snippet formats a known instant and keeps the supplied time zone explicit, so a server's default locale cannot alter the output unexpectedly.",
         cost="Formatting one date is constant work relative to the size of the page, but creating a new formatter for every table cell adds avoidable overhead. Reuse an Intl.DateTimeFormat instance for repeated rows with the same locale and zone. Sorting N events takes O(N log N) with a comparison sort; compare numeric instants rather than reparsing display strings. Localized text also changes width, so test layout with longer labels. Do not assume every person on one site shares a single language or time zone.",
         mistakes=["Do not store a formatted date as the only record of an instant.", "Do not sort by locale-formatted date strings.", "Do not guess a future appointment's time zone from the server."],
         language="javascript", runnable=True, code='''const inspectionInstant = new Date("2026-10-04T09:20:00Z");
const formatter = new Intl.DateTimeFormat("en-IN", {
  timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "short"
});
console.log(formatter.format(inspectionInstant));'''),
    dict(path="web-tech/cursor-pagination", theme=themes[1]["path"], title="Cursor Pagination for Changing Collections",
         summary="Page through records with a stable order and a bounded response size.",
         definition="Pagination bounds the work and transfer of a collection read. Offset pagination is easy to express but may skip or repeat records when new rows arrive before the current page. A cursor based on a stable ordered pair, such as creation time and record ID, says where the next page begins. The server must fix a sort order, validate the cursor, cap the requested page size, and return a next cursor only when more results exist. A cursor is a position marker, not proof of permission; every page still applies the caller's visibility rule.",
         case="A reviewer scrolls an inspection feed sorted by newest creation time, then by ID for ties. While the reviewer reads page one, another inspection arrives. A keyset query for page two starts after the last item from page one, so it does not shift merely because the new row appeared at the front. The response includes 25 records at most and a cursor for the next page. The client should not decode the cursor as a case ID or use it to bypass filters; the server validates its shape and binds the same filters to each page.",
         cost="An indexed keyset scan can seek near the cursor and read roughly O(P) rows for page size P, while a large offset may require scanning or discarding many earlier rows. The sort keys and filter must match an appropriate index. Encoding a cursor is small, but a tamper-resistant cursor may need signing when it carries filter or tenant context. A changing dataset can still alter membership; pagination promises a stable traversal rule, not a frozen snapshot unless the API explicitly provides one.",
         mistakes=["Do not let the client request an unbounded page size.", "Do not sort only by a timestamp that can tie.", "Do not treat a cursor as authorization.", "Do not change filters between pages without restarting the traversal."],
         language="sql", code='''SELECT inspection_id, created_at, summary
FROM inspections
WHERE reviewer_id = :reviewer_id
  AND (created_at, inspection_id) < (:cursor_time, :cursor_id)
ORDER BY created_at DESC, inspection_id DESC
LIMIT :page_limit;'''),
    dict(path="web-tech/idempotent-write-requests", theme=themes[1]["path"], title="Idempotent Write Requests and Lost Responses",
         summary="Make a retry return the first result instead of repeating a side effect.",
         definition="A client timeout does not prove that a write failed. The server may have committed the record and lost only the response. For an operation that must happen once per user intent, accept an idempotency key scoped to the caller and operation. Store the key, request fingerprint, and first result atomically with the effect. A retry with the same key and same input returns that result; the same key with different input is a conflict. Retain keys for a documented window and decide what happens when that window expires. Idempotency is a server contract, not a client delay loop.",
         case="A reviewer creates inspection 93 for case 47. The database commits, but the browser loses the response and retries. The same key returns inspection 93 rather than creating inspection 94. If the note body changed between attempts while the key remained the same, the server responds with a conflict and asks for a new user intent. A simple process-local map demonstrates the decision rule, but production storage must keep key reservation and record creation in one transaction or another atomic boundary across workers.",
         cost="An expected O(1) key lookup adds storage proportional to the number of retained keys, O(K). Hashing a request body of B bytes costs O(B). A transaction adds write latency but prevents a duplicate effect under concurrent retries. Retention expiry saves storage yet reopens the possibility of a duplicate after the window; document that tradeoff. Never key the cache only by an untrusted header without the authenticated caller and route, or two callers could receive each other's result.",
         mistakes=["Do not infer that a timed-out write had no effect.", "Do not reuse one key for different request bodies.", "Do not keep the key map only in one process when requests can reach several workers."],
         language="javascript", runnable=True, code='''const attempts = new Map();
let nextInspectionId = 93;
function createInspection(reviewerId, caseId, key, note) {
  const scope = `${reviewerId}:${caseId}:${key}`;
  const previous = attempts.get(scope);
  if (previous) return previous.note === note ? previous.result : { status: 409 };
  const result = { status: 201, inspectionId: nextInspectionId++ };
  attempts.set(scope, { note, result });
  return result;
}
console.log(createInspection(29, 47, "review-47-19", "seal replaced").inspectionId);
console.log(createInspection(29, 47, "review-47-19", "seal replaced").inspectionId);
console.log(createInspection(29, 47, "review-47-19", "other note").status);'''),
    dict(path="web-tech/background-jobs-and-outbox", theme=themes[1]["path"], title="Background Jobs and the Outbox Boundary",
         summary="Record a business change and its follow-up work together.",
         definition="Some work should not hold an HTTP response open: image conversion, notification delivery, or a long report. A background worker can process it after the request commits. The hard boundary is ensuring that the business record and the instruction to perform follow-up work are not split by a crash. An outbox row written in the same database transaction as the record gives a worker a durable queue to poll. Workers can retry, so handlers must tolerate duplicate delivery and mark work complete only after its effect is safe. A queue is not a guarantee that external side effects happen exactly once.",
         case="An inspection is saved and a reviewer notification is needed. If the service writes the inspection then crashes before publishing a message, the notification disappears. If it publishes first and later rolls back the inspection, the notification refers to a record that does not exist. The transaction sketch writes both the inspection and an outbox event. A worker reads pending events and sends the notification with a stable event ID. If delivery is uncertain, the downstream system needs its own deduplication or reconciliation rule.",
         cost="Writing one outbox row adds one database write per business event and O(E) retained storage for E events until cleanup. Polling too often adds read load; polling too slowly delays delivery. Index pending rows and delete or archive completed work under a retention policy. The request can return promptly after the transaction, but the user-facing state must say 'queued' rather than 'delivered'. Monitor stuck events and retry counts; a silent backlog is a product failure even while API responses remain 201.",
         mistakes=["Do not publish an external event before the business transaction commits.", "Do not promise exactly-once effects from an at-least-once worker.", "Do not display queued work as completed delivery."],
         language="sql", code='''BEGIN;
INSERT INTO inspections (inspection_id, case_id, note)
VALUES (93, 47, 'seal replaced');
INSERT INTO outbox_events (event_id, event_type, record_id, state)
VALUES (581, 'inspection.created', 93, 'pending');
COMMIT;'''),
    dict(path="web-tech/rate-limits-and-request-budgets", theme=themes[1]["path"], title="Rate Limits and Request Budgets",
         summary="Bound work per caller while keeping response behavior predictable.",
         definition="A rate limit bounds how often a caller may perform an operation during a window. It protects shared capacity and discourages automated abuse, but does not replace authentication, authorization, or input limits. Different routes have different costs: a search may be cheap while a report export is expensive. Choose a key that reflects the real caller, then account for proxies and shared clients; raw IP address alone can punish a whole office. The server should return a clear limit response and a retry hint when appropriate. Limits must work across all serving instances or a caller can multiply capacity by reaching several workers.",
         case="A reviewer can open case pages freely but may request only three large exports per minute. The fourth export receives 429 before the database begins the expensive report. A legitimate retry after the window can proceed. The in-memory function below models one process for a test; a production fleet needs a shared counter or service-level limiter. The response should not expose internal account details. Also cap body size and execution time so one allowed request cannot consume unlimited resources.",
         cost="A map lookup and counter update are expected O(1), with O(C) state for C active caller keys. A distributed limiter adds a network round trip and must define behavior when its store is unavailable. Fixed windows can allow bursts at boundaries; token buckets or sliding windows smooth that behavior at greater implementation cost. Decide whether to fail closed or degrade for a critical route. Monitor rejected requests by route and caller class without storing sensitive payloads.",
         mistakes=["Do not use rate limiting as a replacement for permission checks.", "Do not keep independent limits on each worker in a scaled service.", "Do not use one limit for cheap reads and costly exports."],
         language="javascript", runnable=True, code='''const requestWindows = new Map();
function allowExport(reviewerId, nowMs) {
  const windowStart = Math.floor(nowMs / 60000) * 60000;
  const current = requestWindows.get(reviewerId);
  const used = current?.windowStart === windowStart ? current.used : 0;
  if (used >= 3) return { status: 429 };
  requestWindows.set(reviewerId, { windowStart, used: used + 1 });
  return { status: 200 };
}
for (let attempt = 0; attempt < 4; attempt++) {
  console.log(allowExport(29, 120000).status);
}'''),
])

topics.extend([
    dict(path="web-tech/canonical-route-identity", theme=themes[6]["path"], title="Canonical Route Identity",
         summary="Choose one stable public path for a page and handle alternate paths deliberately.",
         definition="A public article can appear through a category path, an old slug, a query variant, or a print view. Choose one canonical route for the main content and make alternate routes redirect or declare their relationship consistently. The canonical target must represent substantially the same page; it is not a way to point thin or unrelated pages at a stronger one. Generate the target from trusted route data, not arbitrary query text. A stable title, description, and initial HTML content help readers and crawlers understand the page before optional scripts run. A canonical hint is a signal, not a substitute for working links and response codes.",
         case="The inspection guide moves from '/guides/old-valve-check' to '/guides/valve-inspection'. Existing bookmarks should reach the new guide through a permanent redirect. The new page uses its own stable canonical location; pagination or filter links remain distinct when they lead to meaningfully different content. A preview draft should not be published under the same canonical path as a live page. The code builds the canonical location from a trusted site origin and route map. The server should emit it in initial HTML alongside a useful page title.",
         cost="One redirect adds a network round trip for visitors who use an old path. Maintaining a route map costs O(R) entries for R historical redirects, so consolidate chains and remove loops. Canonical metadata itself is small, but inconsistent values across server and client renders create difficult diagnostics. Test direct access, redirects, status codes, and final path in the build. A site with many duplicate routes wastes crawl and maintenance work; stable route ownership makes future migrations easier.",
         mistakes=["Do not point unrelated pages at one canonical route.", "Do not build a redirect chain when one hop will do.", "Do not set a client-only canonical different from initial HTML."],
         language="javascript", code='''function canonicalForGuide(siteOrigin, guideSlug) {
  const allowedSlugs = new Set(["valve-inspection", "pump-review"]);
  if (!allowedSlugs.has(guideSlug)) throw new Error("Unknown guide route");
  return new URL(`/guides/${guideSlug}`, siteOrigin).href;
}
const canonicalLocation = canonicalForGuide(process.env.PUBLIC_SITE_ORIGIN, "valve-inspection");'''),
    dict(path="web-tech/structured-data-visible-facts", theme=themes[6]["path"], title="Structured Data from Visible Facts",
         summary="Describe a public article using facts already present in its page content.",
         definition="Structured data is a machine-readable description of page entities and relationships. It should match visible content and the page's actual type. A tutorial article can identify its title, publication state, and author when those facts are real; inventing ratings or authors to fill fields makes the markup misleading. Generate the data from the same content record that renders the visible heading and byline, then validate the serialized shape. Do not make structured data the only place important information appears. It helps interpretation but does not guarantee a special display in search results.",
         case="A public guide displays 'Valve inspection procedure' and a named editorial author. The server constructs one article data object from that exact record and emits a JSON-LD script on the published page. If the guide is still a draft, it is not included in the public page set. If the visible heading changes, the structured title changes with it because both use the same record. A fabricated review count would have no basis in the page and is omitted. The example shows the object boundary; production output must serialize safely into a script element.",
         cost="Creating one small data object is O(1) relative to page size, while JSON serialization is O(B) for B output bytes. The maintenance cost lies in keeping the schema tied to real content fields as templates evolve. Duplicated hardcoded metadata often drifts after an edit. Validate representative pages for required properties and escaping, but do not spend time marking up fields the product does not actually maintain. Structured data cannot repair a 404 route or an empty initial page.",
         mistakes=["Do not invent ratings, dates, or authors to fill markup fields.", "Do not let structured facts disagree with visible page text.", "Do not expect markup alone to guarantee enhanced search display."],
         language="javascript", code='''function articleFacts(contentRecord) {
  if (contentRecord.status !== "published") return null;
  return {
    "@context": contentRecord.schemaContext,
    "@type": "Article",
    headline: contentRecord.title,
    author: { "@type": "Person", name: contentRecord.authorName },
    datePublished: contentRecord.publishedAt
  };
}'''),
    dict(path="web-tech/sitemap-and-index-control", theme=themes[6]["path"], title="Sitemap and Index Control",
         summary="List only canonical public routes and keep drafts out of the published set.",
         definition="A sitemap is an inventory of public canonical routes that a crawler may discover. It is not a guarantee that any page will be indexed, and it should not include draft, private, duplicate, or broken paths. Access control protects private data; crawl instructions do not. A page that must be excluded from indexing needs an appropriate page or response directive while still respecting whether a crawler can fetch that directive. Keep the public route set consistent with redirects, canonical identity, and application status. Generate the inventory from published records rather than manually appending every generated slug.",
         case="A tutorial library has published lesson pages and separate editorial drafts awaiting review. The live sitemap should include a lesson only after it is actually published at a reachable canonical route. A quiz draft belongs in the editorial system, not the public sitemap. If a lesson is renamed, the old path redirects and the sitemap lists only the new canonical path. A private reviewer case never belongs in the public inventory, even if its URL pattern is predictable.",
         cost="Walking N content records to build an inventory takes O(N) time and O(P) output for P published canonical routes. Very large inventories can be split into bounded files, but a small site needs only a straightforward generated list. Validate route status and duplicate paths before export. Indexing behavior is outside the site's direct control, so monitor actual crawl and search behavior instead of treating sitemap generation as proof of visibility.",
         mistakes=["Do not put draft or private pages in a public sitemap.", "Do not use crawl instructions as authentication.", "Do not list old redirect paths alongside the preferred canonical route."],
         language="javascript", runnable=True, code='''const routeRecords = [
  { path: "/guides/valve-inspection", status: "published", canonical: true },
  { path: "/guides/pump-review", status: "draft", canonical: true },
  { path: "/guides/old-valve-check", status: "published", canonical: false }
];
const publicPaths = routeRecords
  .filter(record => record.status === "published" && record.canonical)
  .map(record => record.path);
console.log(publicPaths.join(","));'''),
    dict(path="web-tech/internal-link-architecture", theme=themes[6]["path"], title="Internal Link Architecture for Technical Guides",
         summary="Connect prerequisites, adjacent decisions, and practical projects with real routes.",
         definition="Internal links are part of a learning system. A broad hub should lead to the specific decision a reader needs next; a technical lesson should link to its prerequisite, an adjacent tradeoff, and a project that uses it. A route that exists only in search results or a sitemap is hard to discover and easy to neglect. Link text should name the destination's purpose rather than say 'click here'. Keep links in server-rendered HTML so they remain usable without a client script. Verify that every target resolves to a published route before export.",
         case="A reader lands on cursor pagination while implementing a case feed. The page links back to the API system hub, across to database indexing, and forward to a release test that checks the route. The database lesson links back to the pagination contract, so the relationship works in both directions. A broad Web Development root lists every topic hub and each hub lists its own lessons. A checker walks this graph and flags a lesson that cannot be reached from the root. Adding dozens of pages without that graph would leave a large but fragmented library.",
         cost="For N routes and E internal links, a graph walk and link validation take O(N + E) time and O(N) visited memory. Dense links can distract readers, so connect pages when the relationship explains a real decision rather than adding every route to every page. Route renames require link updates or redirects. Automated checks catch broken targets; editorial review still has to judge whether the link text and placement help the reader.",
         mistakes=["Do not create a route that no hub or lesson reaches.", "Do not use vague link text for every destination.", "Do not point public lessons at draft-only routes."],
         language="javascript", runnable=True, code='''const lessonGraph = new Map([
  ["web-development", ["api-systems", "data-persistence"]],
  ["api-systems", ["cursor-pagination"]],
  ["data-persistence", ["query-indexes"]]
]);
const visited = new Set(["web-development"]);
const pending = ["web-development"];
while (pending.length) {
  for (const next of lessonGraph.get(pending.pop()) ?? []) {
    if (!visited.has(next)) { visited.add(next); pending.push(next); }
  }
}
console.log(visited.size);'''),
])

topics.extend([
    dict(path="web-tech/service-worker-offline-fallback", theme=themes[4]["path"], title="Service Worker Offline Fallback",
         summary="Cache an intentional public shell without caching private case responses.",
         definition="A service worker can intercept eligible requests under its scope and choose a response from the network or a local cache. That power requires a narrow policy. Cache the public application shell and an offline explanation page during installation; do not place authenticated case HTML or API responses into a shared-looking cache by default. Update caches by version and remove obsolete entries during activation. A worker may be stopped between events, so state that must persist belongs in storage, not a global variable. The offline page should explain what remains available and what requires reconnecting.",
         case="An inspector opens the public guide while online, then loses connectivity on a train. The installed worker can serve a previously cached guide shell and an offline message. It must not silently show an old private case as though it were current. A case submission remains pending until a server confirms it. The example handles only a named public guide and an offline page; every other request follows normal browser behavior. A production worker also needs versioned asset lists and upgrade tests across old and new tabs.",
         cost="Caching public shell bytes consumes O(B) local storage for B cached bytes and adds install-time transfer. Each intercepted request adds a small lookup and policy decision; a network-first strategy can still wait on a failing connection unless timeout behavior is defined. Keeping too many revisions wastes device storage and can lead to eviction. Test update and rollback paths, not only first install. A service worker is useful only when it improves a real offline journey.",
         mistakes=["Do not cache private case responses without an explicit privacy policy.", "Do not assume a worker stays alive between events.", "Do not label a stale record as current while offline."],
         language="javascript", code='''const shellCache = "guide-shell-v3";
const offlinePage = "/offline";
self.addEventListener("install", event => {
  event.waitUntil(caches.open(shellCache).then(cache =>
    cache.addAll(["/guides/inspection", offlinePage])));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith("guide-shell-") && key !== shellCache)
      .map(key => caches.delete(key)))));
});
self.addEventListener("fetch", event => {
  const target = new URL(event.request.url);
  if (event.request.method !== "GET" || target.pathname !== "/guides/inspection") return;
  event.respondWith(fetch(event.request).catch(async () =>
    await caches.match(event.request) ?? await caches.match(offlinePage)));
});'''),
    dict(path="web-tech/indexeddb-draft-queue", theme=themes[4]["path"], title="IndexedDB for Local Drafts",
         summary="Keep an unsent inspection draft separate from an accepted server record.",
         definition="IndexedDB can store structured local records without blocking the main thread like a large synchronous localStorage write. A draft queue needs a stable local ID, case ID, body, creation instant, and status such as pending or conflict. Saving locally means only that the device holds the draft; it does not mean the server accepted it. The application must present that distinction clearly, protect sensitive data according to its product policy, and tolerate storage denial or eviction. A transaction groups local writes inside one store, but it cannot make an offline server write atomic.",
         case="An inspector types a note for case 47 while offline. The page saves it under local ID 'draft-47-83' and shows 'Saved on this device; not submitted'. When the network returns, a sync process reads pending drafts and submits them with idempotency keys. If the server reports that the case has changed, the draft moves to conflict instead of disappearing. If local storage is unavailable, the page warns before navigation. The snippet opens a versioned database and writes one draft, but the full product still needs retries, conflict display, and deletion after confirmation.",
         cost="IndexedDB writes are asynchronous, and indexed key lookup is usually much cheaper than scanning a large collection, but latency depends on device storage and transaction size. Keeping D drafts consumes O(D plus body bytes) space until cleanup. Large images should not be copied into every draft record; use a separate bounded storage policy. Schema upgrades can block when old tabs hold open connections, so handle versionchange and test upgrades. Device-local drafts require explicit retention and privacy decisions.",
         mistakes=["Do not call a local draft a completed submission.", "Do not delete a draft before the server confirms its write.", "Do not assume device storage is permanent or always available."],
         language="javascript", code='''const opening = indexedDB.open("inspection-drafts", 2);
opening.onupgradeneeded = () => {
  const database = opening.result;
  if (!database.objectStoreNames.contains("drafts")) {
    database.createObjectStore("drafts", { keyPath: "draftId" });
  }
};
opening.onsuccess = () => {
  const database = opening.result;
  const transaction = database.transaction("drafts", "readwrite");
  transaction.objectStore("drafts").put({
    draftId: "draft-47-83", caseId: 47, note: "seal checked", status: "pending"
  });
};'''),
    dict(path="web-tech/web-app-manifest-and-install", theme=themes[4]["path"], title="Web App Manifest and Optional Installation",
         summary="Describe a useful launch surface while keeping the website usable in a tab.",
         definition="A web app manifest supplies metadata such as a name, start path, display preference, and icons for browsers that support installation. It does not create offline behavior or guarantee an install prompt. The start path must lead to a valid route with appropriate authentication handling; an installed icon should not open a blank client shell when the user is signed out. Keep ordinary web navigation and responsive layout fully usable without installation. Installation is a convenience layer over the site, not a separate permission or data-storage model.",
         case="A reviewer installs the inspection portal on a managed laptop. Launching it opens the case queue route. If the session expired, the server returns a clear sign-in path rather than an empty screen. The manifest icon and short name identify the portal, but drafts remain governed by the same local storage policy as a browser tab. Another reviewer may never install it and should receive the same core workflow. Test the launch route after an update, when offline, and after sign-out before calling the install experience complete.",
         cost="The manifest itself is small, but icons at several resolutions add transfer and storage. Installation support and prompt behavior vary by browser and environment, so code should not require a prompt event to proceed. A start route that loads a large script bundle still has that cost after installation. Cache only assets that help the launch experience and do not use the manifest as a substitute for performance work. Maintain icon files and routes across releases so existing installs keep opening correctly.",
         mistakes=["Do not promise offline use merely because a manifest exists.", "Do not make installation mandatory for the core workflow.", "Do not point start_url at a route the server cannot open directly."],
         language="json", code='''{
  "name": "AI Trove Inspection Portal",
  "short_name": "Inspections",
  "start_url": "/cases",
  "display": "standalone",
  "icons": [
    { "src": "/assets/inspection-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/assets/inspection-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}'''),
    dict(path="web-tech/offline-sync-conflict-policy", theme=themes[4]["path"], title="Offline Sync and Conflict Policy",
         summary="Tell the user when a local edit conflicts with a newer server version.",
         definition="An offline draft can be submitted later, but the server may have changed in the meantime. A sync request should include the version the editor saw and an idempotency key. The server checks permission at sync time, compares versions, and either commits or returns a conflict with enough safe context for reconciliation. Automatically taking the last arriving value can erase another person's work. Some fields can be merged mechanically; a free-text inspection note usually needs a user decision or an append-only model. Preserve the local draft until the result is known.",
         case="Reviewer 29 edits case 47 from version 12 while disconnected. Reviewer 31 approves the case on the server, producing version 13. When reviewer 29 reconnects, the old draft arrives with expected version 12. The server returns 409 and the current version, and the UI shows both the draft and the new status. The reviewer may append the note as a new inspection if policy allows, or discard it. The code models the version check only; a real service must perform comparison and write atomically with authorization.",
         cost="Version comparison is O(1), but a conflict can require an extra read and a human decision. Keeping local drafts consumes storage until confirmation or discard. Automatic merge logic adds complexity proportional to the data model; do not build a general merge engine for a small append-only workflow. Repeated retries should carry one stable idempotency key so a delayed response cannot create duplicates. Monitor conflict frequency to find workflows that need better collaboration design.",
         mistakes=["Do not let last arrival silently overwrite a newer edit.", "Do not drop a local draft after a 409 response.", "Do not bypass current server permission because a draft was once allowed."],
         language="javascript", runnable=True, code='''function acceptDraft({ expectedVersion, currentVersion, note }) {
  if (expectedVersion !== currentVersion) {
    return { status: 409, currentVersion };
  }
  if (!note.trim()) return { status: 422 };
  return { status: 201, version: currentVersion + 1 };
}
console.log(acceptDraft({ expectedVersion: 12, currentVersion: 13, note: "seal checked" }).status);
console.log(acceptDraft({ expectedVersion: 13, currentVersion: 13, note: "seal checked" }).version);'''),
    dict(path="web-tech/environment-config-and-secrets", theme=themes[5]["path"], title="Environment Configuration and Secret Boundaries",
         summary="Validate required settings at startup and keep credentials out of client bundles.",
         definition="Configuration tells one application build which services and limits to use in a specific environment. Secrets are a narrower class of configuration that grant access and must stay on trusted servers or secret stores. A browser bundle is public even if a variable name contains 'secret'. Validate required server settings at startup so a missing database name fails early, not during a user request. Rotate credentials without committing them to source control, and restrict each service identity to the operations it needs. Separate local, staging, and production values so a test job cannot accidentally write to live data.",
         case="A case API deployment receives a database address and signing key from its runtime environment. Startup checks that both are present and that the signing key meets a length requirement before accepting traffic. The public frontend receives only a non-secret API path. A developer who needs to diagnose a failure logs which setting is missing, not its value. If a credential is compromised, the team rotates it and verifies the old one no longer works. The code demonstrates validation, not a particular secret-management product.",
         cost="Startup validation is O(1) for a fixed set of settings. Secret rotation may require a period when both old and new signing keys are recognized, plus careful expiry of old sessions. A central secret service adds network and operational cost but can improve access control and auditability. Injecting secrets at build time into a browser app leaks them regardless of minification. Keep the number of long-lived secrets small and test staging with credentials that cannot reach production resources.",
         mistakes=["Do not put credentials in a browser bundle or repository fixture.", "Do not print secret values in startup errors.", "Do not let staging credentials write production data."],
         language="javascript", code='''function readServerConfig(environment) {
  const databaseAddress = environment.CASE_DATABASE_ADDRESS;
  const sessionSigningKey = environment.SESSION_SIGNING_KEY;
  if (!databaseAddress) throw new Error("Missing case database address");
  if (!sessionSigningKey || sessionSigningKey.length < 32) {
    throw new Error("Session signing key is not configured safely");
  }
  return { databaseAddress, sessionSigningKey };
}
const serverConfig = readServerConfig(process.env);'''),
    dict(path="web-tech/ci-release-gates", theme=themes[5]["path"], title="Continuous Integration and Release Gates",
         summary="Run fast content and code checks before a candidate becomes a release.",
         definition="A release gate is a repeatable check tied to behavior the application promises. Static analysis and a build catch syntax and bundling faults; content checks catch broken internal routes; contract tests catch wrong status or persistence behavior. A small browser journey can verify keyboard submission and visible errors. The deployment process should refuse a candidate when a required gate fails, then run a read-only smoke check after release. Do not make a green pipeline the only proof of quality: production traffic, configuration, and data may differ from CI.",
         case="A new case lesson links to a route that does not exist. The content checker fails before the site bundle is produced. A server change that turns an unauthorized write into a 200 fails a contract test. A candidate that passes both can be deployed to a staging environment for a keyboard form check, then promoted. Immediately after production deployment, a read-only probe checks the case page and API. If that probe fails, rollout stops and the previous compatible version is restored. Each gate reports the failing contract instead of a vague 'pipeline red' message.",
         cost="Every gate consumes runtime, so order cheap deterministic checks before expensive browser work. A build's complexity depends on source and dependency graph size; integration tests add database setup and network time. Cache dependencies carefully without caching away the actual test result. Flaky tests impose a hidden cost because people learn to ignore failures; isolate data, fix race conditions, and keep critical gates trustworthy. A parallel pipeline can reduce wall time while preserving clear failure attribution.",
         mistakes=["Do not bypass a required gate to make a release look green.", "Do not let tests write into live customer data.", "Do not treat a passing local build as proof of the deployed route."],
         language="bash", code='''set -euo pipefail
npm ci
python3 scripts/check-web-development-content.py
npm run build
# Run isolated API and browser contract suites before promotion.'''),
    dict(path="web-tech/horizontal-scale-and-shared-state", theme=themes[5]["path"], title="Horizontal Scale and Shared State",
         summary="Keep case requests correct when successive calls reach different workers.",
         definition="Adding more service instances increases capacity only when they agree on durable state and authorization decisions. A process-local session map or idempotency cache works in one worker and fails when the next request reaches another. Store shared sessions, records, counters, and idempotency results in systems designed for that scope. A load balancer distributes requests, but sticky routing is not a substitute for clear state ownership or failure recovery. Plan for workers to restart at any time. The same case write must remain correct no matter which healthy instance receives it.",
         case="A reviewer signs in through worker A, then submits case 47 through worker B. If session state lives only in A's memory, B reports an unexpected sign-out. A shared session store lets B validate the same opaque cookie. If a retry reaches worker C, an idempotency record in durable shared storage returns the first result. The application can scale reads and writes independently only after its storage and transaction contracts support that traffic. The injected service interfaces below keep request handling independent of the process that receives it.",
         cost="Each shared-state lookup adds network latency and load to the store. More app workers can make a database the bottleneck; pool connections and measure queueing, not only CPU. Replication lag affects reads that expect a just-committed write, so decide when a primary read is required. Stateless application processes simplify replacement, but the system still has state in databases, caches, queues, and object storage. Capacity testing should include failover and mixed worker versions during rollout.",
         mistakes=["Do not store critical sessions only in one worker's memory.", "Do not assume sticky routing is a durability strategy.", "Do not add app instances without measuring shared-store capacity."],
         language="javascript", code='''async function handleCaseRead(request, sessionStore, caseStore) {
  const session = await sessionStore.get(request.sessionId);
  if (!session) return { status: 401 };
  const allowed = await caseStore.canRead(session.reviewerId, request.caseId);
  if (!allowed) return { status: 403 };
  const record = await caseStore.get(request.caseId);
  return record ? { status: 200, record } : { status: 404 };
}'''),
    dict(path="web-tech/backup-restore-drill", theme=themes[5]["path"], title="Backup and Restore Drills",
         summary="Prove a protected copy can recover a case record within a stated window.",
         definition="A backup is a recovery promise, not merely a file written by a scheduled job. Define how much data loss is tolerable and how long the service may be unavailable, then select backup frequency and restore procedures accordingly. Protect the copy from the same credentials and failure domain as the live database. A restore drill uses an isolated environment to verify that the file is readable, schema migrations are compatible, and a known case can be queried. Record the elapsed time and any manual steps. Do not test a restore by overwriting production data.",
         case="A nightly case database snapshot exists, but no one has restored it. During a drill, the team restores it to a separate test database, runs the application migration compatibility checks, and confirms case 47 plus its inspection 93 are present. The measured restore takes 42 minutes, longer than the team's 30-minute recovery target. That gap prompts a change in backup design or recovery procedure. Merely seeing a successful backup job in a dashboard would not have revealed the delay or a missing encryption key.",
         cost="A full snapshot transfers O(B) bytes for database size B and consumes comparable protected storage, with additional space for retention. Frequent backups reduce potential data loss but increase transfer and storage cost. Incremental approaches reduce repeated bytes while making restore chains more complex. A drill consumes isolated compute time but turns an assumption into evidence. Test credential access, decryption, schema version, and application reads as part of recovery; a raw database restore alone may not restore the service.",
         mistakes=["Do not treat backup success as proof of restore success.", "Do not store the only backup under the same failure and access boundary as production.", "Do not run a restore drill against the live database."],
         language="bash", code='''set -euo pipefail
pg_dump --format=custom --file="${BACKUP_OUTPUT_PATH}" "${SOURCE_DATABASE_URL}"
pg_restore --list "${BACKUP_OUTPUT_PATH}" > "${BACKUP_CATALOG_PATH}"
# Restore only into an isolated test database with separate credentials.
pg_restore --dbname="${RESTORE_TEST_DATABASE_URL}" "${BACKUP_OUTPUT_PATH}"'''),
])

topics.extend([
    dict(path="web-tech/relational-record-modeling", theme=themes[2]["path"], title="Relational Records and Database Constraints",
         summary="Express case ownership and inspection identity in the schema, not only in forms.",
         definition="A relational model names the entities and relationships that must remain true after every request. A case has a stable ID; an inspection belongs to one case; a reviewer assignment connects one reviewer to one case. Primary keys prevent duplicate identity, foreign keys prevent orphaned inspections, and check constraints can reject values that should never enter storage. Application validation still provides clear user messages and permission checks, but a database constraint protects the invariant when another process writes to the same table. Design the schema from real operations rather than placing an entire case in one unvalidated text field.",
         case="Case 47 has two inspection entries and reviewer 29 is assigned to it. A write for a nonexistent case cannot create an orphan inspection because the foreign key rejects it. A duplicate assignment pair cannot be inserted twice. The server checks that reviewer 29 may write before opening the transaction; the database cannot infer that policy merely from the foreign key. If an inspection must never be edited after approval, that rule requires a separate state transition policy. The schema below encodes identity and relationship, not every business permission.",
         cost="Each index and foreign key check adds work to writes and storage proportional to row count. Reads for a case's inspections need an index on case_id when the table grows. Normalized rows reduce repeated case data but require joins to assemble a page. Measure query plans at realistic sizes rather than assuming a small development table predicts production behavior. A constraint error should be translated into a safe API response; never expose raw database exception text to the browser.",
         mistakes=["Do not rely only on a form field to preserve a database invariant.", "Do not use a foreign key as a reviewer permission check.", "Do not store every inspection as an unstructured blob inside one case row."],
         language="sql", code='''CREATE TABLE cases (
  case_id bigint PRIMARY KEY,
  title text NOT NULL
);
CREATE TABLE inspections (
  inspection_id bigint PRIMARY KEY,
  case_id bigint NOT NULL REFERENCES cases(case_id),
  note text NOT NULL CHECK (char_length(note) BETWEEN 1 AND 160)
);
CREATE TABLE reviewer_assignments (
  reviewer_id bigint NOT NULL,
  case_id bigint NOT NULL REFERENCES cases(case_id),
  PRIMARY KEY (reviewer_id, case_id)
);'''),
    dict(path="web-tech/transactions-and-concurrent-writes", theme=themes[2]["path"], title="Transactions and Concurrent Writes",
         summary="Keep a multi-step update atomic and reject stale edits deliberately.",
         definition="A transaction groups several database changes so they commit together or not at all. It does not automatically resolve every race between two people editing the same record. An optimistic version field lets a write state which version it read. The database updates only when that version still matches; a zero-row update means the editor is stale and must reconcile. A transaction can then add an inspection note and advance the case version together. Isolation level, constraints, and retry policy still matter. Retrying the entire transaction after a serialization failure is different from blindly repeating an external side effect.",
         case="Two reviewers open case 47 at version 6. Reviewer 29 saves first and advances it to 7. Reviewer 31's update with expected version 6 affects no row and receives a conflict state rather than overwriting the first note. The interface can show the current record and let reviewer 31 decide what to do. If a transaction also queues a notification, the queue instruction belongs in the same database boundary. An email sent before commit would be impossible to roll back if the record write failed.",
         cost="A version comparison is O(1) per indexed row but may wait on a concurrent lock. A transaction keeps locks or a snapshot until commit, so long transactions reduce throughput and raise contention. Retrying after conflict adds work; cap retries and surface a user choice when edits are semantic, not automatically mergeable. The SQL shows a compare-and-swap update. The application must check whether a row was returned before inserting dependent work and committing.",
         mistakes=["Do not assume a transaction prevents lost updates without a concurrency rule.", "Do not send irreversible external effects before commit.", "Do not retry a human edit conflict as though it were a transient database error."],
         language="sql", code='''UPDATE cases
SET status = 'reviewed', version = version + 1
WHERE case_id = 47 AND version = 6
RETURNING case_id, version;
-- A zero-row result is a conflict; do not insert dependent work.'''),
    dict(path="web-tech/indexes-and-query-plans", theme=themes[2]["path"], title="Indexes and Query Plans for Case Feeds",
         summary="Match an index to the actual filter and sort used by a route.",
         definition="An index is an alternate path to rows, not a universal speed switch. A case feed filtered by reviewer and sorted by creation time can use an index that begins with reviewer_id and continues with the order keys. The database planner may still choose a table scan for a tiny table or broad filter. Inspect a plan with representative row counts and parameters; compare rows examined, sorting, and I/O. Indexes consume storage and slow writes because each changed row updates index entries. Add one to support a measured query pattern, not every column that appears in a schema.",
         case="A reviewer feed for reviewer 29 returns the newest 25 inspections. Without a matching index, the server may scan many rows and sort them before applying the limit. An index on reviewer_id, created_at descending, and inspection_id descending can support the filter and stable order used by the cursor query. If the endpoint filters by case status from a different table, the plan may still need a join. Inspect that complete query rather than claiming the index alone solves every delay.",
         cost="A B-tree lookup is often O(log N) to find a position, followed by work for the P returned rows, but actual latency depends on cache, visibility checks, and I/O. Index maintenance adds write amplification and disk use as N grows. A covering index can avoid some table reads but becomes wider. Start with EXPLAIN on a representative query; use ANALYZE only when it is safe to execute the query in that environment. Recheck plans after data distribution changes.",
         mistakes=["Do not assume every query uses a newly created index.", "Do not add a wide index without accounting for write and storage cost.", "Do not benchmark only an empty development table."],
         language="sql", code='''CREATE INDEX inspections_reviewer_feed_idx
ON inspections (reviewer_id, created_at DESC, inspection_id DESC);
EXPLAIN (ANALYZE, BUFFERS)
SELECT inspection_id, created_at, summary
FROM inspections
WHERE reviewer_id = 29
ORDER BY created_at DESC, inspection_id DESC
LIMIT 25;'''),
    dict(path="web-tech/expand-and-contract-migrations", theme=themes[2]["path"], title="Expand-and-Contract Schema Migrations",
         summary="Change stored data while old and new application versions overlap.",
         definition="A deployed service may have old and new application instances running at the same time. A safe schema change first expands what storage can hold, then migrates data, then changes readers and writers, and only later removes the old shape. Adding a required column and immediately expecting all old writers to populate it can break requests during rollout. Backfill work should run in bounded batches and report progress. Before dropping an old column, verify that no supported application version or job still reads it. A migration is an operational sequence, not only a SQL file.",
         case="The inspection table gains a normalized reviewer_id column. First add it nullable and deploy code that can read either the new value or the older legacy_reviewer_id field. Backfill existing inspections in batches. Next deploy writers that always set reviewer_id, validate the backfill, and enforce the new non-null constraint. Only after the previous app version is retired should the old read path disappear. If rollback is required during the overlap, the older version still reads records. A one-step rename would make that rollback much harder.",
         cost="A full-table backfill touches O(N) rows and may create significant I/O, locks, and replication lag. Batching reduces peak pressure but extends the coexistence period and adds progress tracking. Each compatibility branch adds temporary application complexity; remove it after the contract stage is complete. Test the old and new binaries against the expanded schema. A code rollback cannot reverse an incompatible data transformation by itself.",
         mistakes=["Do not drop a field while a supported old version still reads it.", "Do not make a large backfill one unbounded transaction.", "Do not treat code rollback as a complete database rollback."],
         language="sql", code='''ALTER TABLE inspections ADD COLUMN reviewer_id bigint;
-- Backfill in bounded batches and verify remaining NULL rows.
WITH batch AS (
  SELECT inspection_id FROM inspections
  WHERE reviewer_id IS NULL AND legacy_reviewer_id IS NOT NULL
  ORDER BY inspection_id LIMIT 250 FOR UPDATE SKIP LOCKED
)
UPDATE inspections
SET reviewer_id = inspections.legacy_reviewer_id
FROM batch WHERE inspections.inspection_id = batch.inspection_id;
-- Enforce NOT NULL only after the new writer is deployed and data is verified.'''),
    dict(path="web-tech/safe-file-upload-pipeline", theme=themes[3]["path"], title="Safe File Upload Pipeline",
         summary="Accept an inspection photo only after bounded parsing, permission, and type checks.",
         definition="A file upload crosses a larger trust boundary than a short text field. The browser can send multipart data, but the filename, declared media type, and bytes are all caller-controlled. The server must authenticate and authorize the case, cap request size before buffering, inspect the actual file format, assign a generated storage name, and keep untrusted bytes away from executable paths. If scanning or conversion runs later, the record should show a pending state until the file is ready. Do not publish a raw upload at a predictable path merely because the filename ends in an allowed extension.",
         case="A reviewer uploads a pump image for case 47. The page's native multipart form still works if JavaScript fails. The server rejects a 29-megabyte file when the policy allows 8 megabytes, even if the browser input accepts it. It checks reviewer permission and the decoded image type, stores it under a generated ID, and creates a separate display variant. A file that claims to be JPEG but contains another format is not trusted. If later processing fails, the case record retains a clear pending or failed attachment state instead of a broken public link.",
         cost="Upload transfer, virus scanning, and image decode are O(B) or more for B input bytes; decoded images can consume far more memory than their compressed file size. Streaming to bounded temporary storage prevents one request from holding the whole file in process memory. Generated variants add storage but reduce repeated download cost. Rate-limit upload endpoints separately from simple reads. Keep retention and deletion rules so abandoned files do not accumulate indefinitely.",
         mistakes=["Do not trust the browser-supplied Content-Type or filename alone.", "Do not buffer an unlimited file before checking size.", "Do not serve unverified uploads from an executable public directory."],
         language="html", code='''<form action="/cases/47/photos" method="post" enctype="multipart/form-data">
  <label for="inspection-photo">Inspection photo</label>
  <input id="inspection-photo" name="photo" type="file" accept="image/jpeg,image/png" required>
  <button type="submit">Upload photo</button>
</form>'''),
    dict(path="web-tech/image-variants-and-delivery", theme=themes[3]["path"], title="Image Variants and Delivery Budgets",
         summary="Serve pixels suited to the display box while reserving stable layout space.",
         definition="An image should be sized for the role it plays on a page. A thumbnail in a case list does not need the same pixels as a detailed inspection view. Generate bounded variants after validating the source file, then let the browser choose from a srcset matched to rendered widths. Include intrinsic width and height to reserve space before loading. The alt text should describe information the image conveys; decorative images can have empty alt text. A picture element can select an alternate format, but do not assume every format is supported by every client without a fallback.",
         case="The same pump image appears in a 180-pixel list card and a 720-pixel case detail. Serving the original 4000-pixel upload to every list visitor wastes transfer and decode work. A small list variant and a larger detail variant keep the pixels proportional to use. The page declares the image's display ratio so the case title does not jump when it loads. A cropped variant must preserve the part of the pump the reviewer needs to inspect; automated compression cannot decide that editorial detail.",
         cost="Encoding several variants takes CPU and O(sum of variant bytes) storage per source image. At request time, a smaller variant reduces transfer and decode cost; browser selection still depends on sizes, viewport, and pixel density. An image CDN can cache variants, but cache keys and invalidation matter when a photo is replaced. Measure actual transferred bytes and visual quality on target devices. Do not lazy-load the first important image without checking whether it delays useful content.",
         mistakes=["Do not serve the original upload for every thumbnail.", "Do not omit dimensions and allow late layout movement.", "Do not write alt text that only repeats 'image' or a filename."],
         language="html", code='''<img src="/assets/pump-47-720.webp"
  srcset="/assets/pump-47-360.webp 360w, /assets/pump-47-720.webp 720w"
  sizes="(max-width: 48rem) 90vw, 720px"
  width="720" height="405"
  alt="Pump 47 with the inspection seal visible beside the outlet">'''),
    dict(path="web-tech/sse-and-websocket-choice", theme=themes[3]["path"], title="Server-Sent Events or WebSocket for Live Views",
         summary="Choose one-way events or two-way messages from the actual interaction contract.",
         definition="A live page may need the server to push updates, the client to send frequent messages, or both. Server-sent events provide a one-way stream from server to browser over HTTP and fit a status feed that the user only reads. WebSocket provides a two-way connection when both sides exchange low-latency messages. Neither removes the need for authentication, per-record authorization, reconnect policy, and stale event handling. Start with polling when update frequency is low; a persistent connection has server and proxy costs. Define event IDs and payload shape before selecting a transport.",
         case="A case queue needs to show that inspection 93 changed to approved within seconds. The browser does not send live edits; a one-way event stream is enough. The page opens an EventSource for case 47 and updates a status node when a validated event arrives. If the connection closes, the browser can reconnect, but the server must support a safe resume or full refresh. A collaborative annotation board with continuous edits in both directions would justify a different transport. A live UI should still show an initial state from a normal page or read request.",
         cost="A persistent stream keeps a connection and server resources open for each active reader. Fan-out work can approach O(C) per event for C connected clients unless an intermediary distributes it. Polling costs repeated requests even when nothing changes; choose based on measured frequency and infrastructure constraints. A slow consumer needs buffering limits so memory cannot grow without bound. On page exit, close the stream to release resources. The snippet updates text, not HTML, and leaves the initial case view intact.",
         mistakes=["Do not select WebSocket for a read-only status page without a need for two-way messages.", "Do not assume reconnecting guarantees no lost events.", "Do not insert event payloads as untrusted HTML."],
         language="javascript", code='''const statusNode = document.querySelector("#case-status");
const updates = new EventSource("/cases/47/events");
updates.addEventListener("status", (event) => {
  const payload = JSON.parse(event.data);
  if (payload.caseId !== 47 || typeof payload.status !== "string") return;
  statusNode.textContent = payload.status;
});
addEventListener("pagehide", () => updates.close());'''),
    dict(path="web-tech/live-update-reconnect-and-order", theme=themes[3]["path"], title="Live Update Reconnect and Event Ordering",
         summary="Reject older status events and reconcile gaps after a stream restarts.",
         definition="A live connection can drop while the server continues to change records. The client needs a version or event sequence so it can recognize an older update and a gap. An event ID allows a stream implementation to resume when the server retains history; otherwise the client must refetch the current record after reconnect. A message's arrival order is not always the business order across workers or transports. The UI should apply an event only when its version is newer than the version already displayed, then decide what to do if versions jump.",
         case="Case 47 is at version 12. The browser receives an approval event for version 14 after a temporary disconnect, but never saw version 13. It fetches the current case snapshot before displaying the final status. Later, a delayed version-13 event arrives and is discarded. A simple counter in one browser tab models the decision; the server must create durable monotonically ordered versions for each case. A timestamp from a client device is not a reliable ordering key for concurrent server writes.",
         cost="Comparing versions is O(1) per event. Keeping replay history costs O(E) storage for E retained events and requires an expiry policy. A gap-triggered snapshot fetch adds a network request, but avoids displaying a state assembled from missing changes. A busy stream should batch or coalesce status updates so DOM work does not overwhelm interaction. If the service cannot provide durable event history, document that reconnect always performs a fresh read rather than pretending every event will be replayed.",
         mistakes=["Do not overwrite a newer status with a delayed old event.", "Do not use client wall-clock time as the authoritative sequence.", "Do not assume reconnect automatically replays every missed event."],
         language="javascript", runnable=True, code='''let visibleVersion = 12;
function classifyUpdate(incomingVersion) {
  if (incomingVersion <= visibleVersion) return "stale";
  if (incomingVersion > visibleVersion + 1) return "refresh snapshot";
  visibleVersion = incomingVersion;
  return "apply";
}
console.log(classifyUpdate(14));
visibleVersion = 14; // Version obtained from the refreshed case snapshot.
console.log(classifyUpdate(13));
console.log(classifyUpdate(12));'''),
])

assert len(themes) == 7 and len(topics) == 28
assert len({item["path"] for item in topics}) == len(topics)
for theme in themes:
    assert sum(topic["theme"] == theme["path"] for topic in topics) == 4, theme["path"]


def add_entry(path, title, summary, entry_type, section_path, sort_order):
    assert path not in by_path, path
    template_path = "web-tech/getting-started" if entry_type == "article" else "web-tech/web-technology"
    entry = copy.deepcopy(by_path[template_path])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), type=entry_type,
                 path=path, title=title, summary=summary, category="Web Development",
                 subject="web-tech", difficulty="Intermediate" if entry_type == "article" else None,
                 tags=["web-tech", "web-development"], sort_order=1100 + sort_order,
                 status="published", created_at=stamp, updated_at=stamp, published_at=stamp,
                 body="")
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": section_path,
                     "content_format": "html", "seo_ready": False}
    if entry_type == "article":
        entry["data"].update(kind="tutorial", author_path="authors/aitrove-editorial", reading_minutes=8)
    entries.append(entry)
    by_path[path] = entry
    return entry


for number, theme in enumerate(themes):
    add_entry(theme["path"], theme["title"], theme["summary"], "subject", theme["path"], number)
for number, topic in enumerate(topics):
    add_entry(topic["path"], topic["title"], topic["summary"], "article", topic["theme"], 10 + number)


def link(path, title=None):
    assert path in by_path, path
    assert by_path[path]["status"] == "published", path
    label = title or by_path[path]["title"]
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(label)}</a>'


def para(value):
    return "<p>" + html.escape(value) + "</p>"


def related_paths(topic):
    theme = next(item for item in themes if item["path"] == topic["theme"])
    siblings = [item["path"] for item in topics if item["theme"] == theme["path"] and item["path"] != topic["path"]]
    return [theme["path"]] + siblings + theme["bridge"]


runnable_count = 0
for topic in topics:
    entry = by_path[topic["path"]]
    code = topic["code"]
    language = topic["language"]
    if language == "javascript":
        subprocess.run(["node", "--check", "--input-type=commonjs"], input=code, text=True,
                       capture_output=True, check=True)
    elif language == "json":
        json.loads(code)
    elif language == "bash":
        subprocess.run(["bash", "-n"], input=code, text=True, capture_output=True, check=True)
    body = para(topic["definition"])
    body += "<h2>Working case</h2>" + para(topic["case"])
    body += f'<h2>Implementation</h2><pre><code class="language-{language}">' + html.escape(code, quote=False) + '</code></pre>'
    if topic.get("runnable"):
        assert language == "javascript", topic["path"]
        result = subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True)
        body += '<h3>Observed output</h3><pre><code class="language-text">' + html.escape(result.stdout.rstrip()) + '</code></pre>'
        runnable_count += 1
    body += "<h2>Cost and boundaries</h2>" + para(topic["cost"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in topic["mistakes"]) + "</ul>"
    related = related_paths(topic)
    body += "<h2>Connected lessons</h2><p>" + "; ".join(link(path) for path in related) + ".</p>"
    entry["body"] = body
    entry["data"].update(related=related,
                         reading_minutes=max(6, round(len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", body))) / 155)))

for theme in themes:
    entry = by_path[theme["path"]]
    group = [item for item in topics if item["theme"] == theme["path"]]
    entry["data"]["modules"] = [{"title": theme["title"], "summary": theme["summary"],
                                 "lessons": [item["path"] for item in group]}]
    entry["data"]["resource_tabs"] = [
        {"title": "Web Development", "path": "web-tech/web-technology"},
        {"title": "Projects", "path": "web-tech/web-technology/project"},
        {"title": "Quizzes", "path": "web-tech/quizzes"}]
    body = para(theme["overview"])
    body += "<h2>Topics in this track</h2><ul>" + "".join(
        f'<li>{link(item["path"])} — {html.escape(item["summary"])}</li>' for item in group) + "</ul>"
    body += "<h2>Connect with existing lessons</h2><p>" + "; ".join(link(path) for path in theme["bridge"]) + ".</p>"
    body += "<h2>Other broad tracks</h2><p>" + "; ".join(link(item["path"]) for item in themes if item != theme) + ".</p>"
    entry["body"] = body

root_entry = by_path["web-tech/web-technology"]
new_modules = [{"title": theme["title"], "summary": theme["summary"],
                "lessons": [theme["path"]] + [item["path"] for item in topics if item["theme"] == theme["path"]]}
               for theme in themes]
root_entry["data"]["modules"].extend(new_modules)
root_entry["body"] += '<h2>Broader Web Development tracks</h2><p>These tracks extend the browser-to-service path into application structure, durable data, live and offline behavior, deployment, and public content architecture. Each hub provides four specific decisions to study and connects back to the earlier lessons.</p>'
for theme in themes:
    group = [item for item in topics if item["theme"] == theme["path"]]
    root_entry["body"] += f'<h2>{link(theme["path"], theme["title"])}</h2><p>{html.escape(theme["summary"])}</p><ul>' + "".join(
        f'<li>{link(item["path"])} — {html.escape(item["summary"])}</li>' for item in group) + '</ul>'
root_entry["updated_at"] = stamp

broader_links = {
    "web-tech/request-and-browser-foundations": [themes[1]["path"], themes[2]["path"], themes[6]["path"]],
    "web-tech/browser-interactions": [themes[0]["path"], themes[3]["path"], themes[4]["path"]],
    "web-tech/state-and-trust": [themes[2]["path"], themes[1]["path"], themes[4]["path"]],
    "web-tech/quality-and-release": [themes[5]["path"], themes[6]["path"], themes[0]["path"]],
    "web-tech/fetch-status-and-abort": ["web-tech/cursor-pagination", "web-tech/sse-and-websocket-choice"],
    "web-tech/form-server-validation": ["web-tech/relational-record-modeling", "web-tech/idempotent-write-requests"],
    "web-tech/browser-storage-boundary": ["web-tech/indexeddb-draft-queue", "web-tech/offline-sync-conflict-policy"],
    "web-tech/cache-etag-revalidation": ["web-tech/service-worker-offline-fallback", "web-tech/canonical-route-identity"],
    "web-tech/release-smoke-and-rollback": ["web-tech/ci-release-gates", "web-tech/backup-restore-drill"],
    "web-tech/record-level-authorization": ["web-tech/relational-record-modeling", "web-tech/horizontal-scale-and-shared-state"],
    "web-tech/performance-budget-and-layout-stability": ["web-tech/image-variants-and-delivery", "web-tech/indexes-and-query-plans"],
}
for path, targets in broader_links.items():
    entry = by_path[path]
    entry["body"] += "<h2>Broader connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": len(themes), "new_lessons": len(topics),
                  "new_runnable_examples": runnable_count,
                  "web_development_routes": sum(entry["path"].startswith("web-tech/") for entry in entries)}))

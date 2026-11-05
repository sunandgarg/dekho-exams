"""Replace Web Technology previews with an integrated web-development curriculum."""

import copy
import datetime
import html
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
subject_root = "web-tech/web-technology"
project_hub = "web-tech/web-technology/project"
quiz_hub = "web-tech/quizzes"
stamp = datetime.datetime.now(datetime.UTC).isoformat()

sections = [
    ("web-tech/request-and-browser-foundations", "Requests and Browser Foundations", "From a URL and request to a parsed page."),
    ("web-tech/browser-interactions", "Browser Interactions", "Events, fetch, and real form submission contracts."),
    ("web-tech/state-and-trust", "State and Trust", "Sessions, local storage, and cache validation boundaries."),
    ("web-tech/quality-and-release", "Quality and Release", "Accessibility, performance, and deploy verification."),
]

lessons = [
    dict(path="web-tech/http-request-response-contract", section=sections[0][0],
         title="HTTP requests: keep method, status, and body contracts separate",
         summary="Route a read and a write through explicit request and response rules.",
         definition="An HTTP request carries a method, target, headers, and sometimes a body. The server answers with a status, headers, and an optional representation. A method is an operation contract, not a decorative prefix on a URL. A retrieval endpoint should not change server state merely because its path contains an action word; a write endpoint should validate input before it records a change. A status tells the client whether to handle a result, missing resource, validation error, or server failure. The response body can explain the result, but clients must not infer success from the presence of JSON alone. This small router models GET as a read and POST as a bounded write. It returns concrete status codes and records only validated messages.",
         case="A maintenance board stores one pump report under ID 47. Reading it returns status 200 and the saved text. Asking for report 83 returns 404. Posting a blank report returns 422 and leaves storage unchanged; posting a valid report returns 201 with the new ID. The caller must distinguish a 404 from a temporary network failure because retrying one cannot create a missing report. A real server would also authenticate the caller, limit body size, and persist the record; the in-memory dictionary here isolates method and status behavior.",
         cost="Dictionary reads and writes take expected O(1) time for a bounded key and use O(N) storage for N reports. Validation scans the submitted message, so its time is O(L) for message length L. Network transfer and serialization add costs not represented by this synchronous model. A response should include an appropriate content type and a bounded payload; this example prints only status and record ID to keep the trace deterministic. HTTP method semantics remain relevant even if a client library hides the wire format.",
         mistakes=["Do not perform a state-changing write behind a GET endpoint.", "Do not treat every response containing JSON as a success.", "Do not return 201 when validation prevented creation.", "Do not retry a missing-resource response as though it were a transport interruption."],
         language="javascript", runnable=True,
         code='''const reports = new Map([[47, "pump checked"]]);
function handleRequest(method, reportId, message) {
  if (method === "GET") {
    return reports.has(reportId)
      ? { status: 200, body: reports.get(reportId) }
      : { status: 404, body: "Report not found" };
  }
  if (method !== "POST") return { status: 405, body: "Method not allowed" };
  if (typeof message !== "string" || !message.trim() || message.length > 160) {
    return { status: 422, body: "Report text is required" };
  }
  if (reports.has(reportId)) return { status: 409, body: "Report already exists" };
  reports.set(reportId, message.trim());
  return { status: 201, body: reportId };
}
console.log(handleRequest("GET", 47).status);
console.log(handleRequest("POST", 83, "  ").status);
console.log(handleRequest("POST", 83, "valve inspected").status);
console.log(reports.get(83));''',
         related=["html/forms-get-post", "javascript/javascript-tutorial", "web-tech/form-server-validation", "web-tech/fetch-status-and-abort"]),
    dict(path="web-tech/url-origin-and-query-boundary", section=sections[0][0],
         title="URLs and origins: separate location, query, and fragment",
         summary="Read a browser location without confusing navigation state with server input.",
         definition="A URL identifies a resource and can also carry query parameters and a fragment. The origin is the scheme, host, and port; a path and query do not change that origin. Query values are transmitted with the request target and may appear in logs, history, and shared links. A fragment is browser-side navigation state and is not included in the HTTP request target. The URL API parses and encodes components, avoiding hand-built strings whose escaping rules are easy to get wrong. A browser script should derive a relative request from the current origin, then choose only the query values the server expects. Same-origin restrictions govern script access to other origins; they are not an authorization system for the server's own endpoints.",
         case="A case-search page reads a term entered as 'pump & valve'. URLSearchParams encodes the ampersand as data, so the server receives one term instead of two accidental parameters. A section fragment can scroll to results without changing the case-search request. Changing the port changes the origin even when the host text stays the same. The example uses a relative path and browser location as its base; it does not embed an external host in code. An attacker may still edit every query field, so the server must validate the term and authorize any result independently.",
         cost="Constructing a query is O(L) in the total encoded input length. Parsing the resulting URL is O(U) in URL length; the browser supplies the parser rather than manual delimiter scans. A query is convenient for bookmarkable reads, but it is inappropriate for secrets or oversized state. Repeated parameters require an explicit policy: get returns one value, while getAll preserves the full list. The example's length check protects the user flow but does not replace server-side limits.",
         mistakes=["Do not put secrets in a query string.", "Do not assume a fragment reaches the server with the request.", "Do not build query strings by concatenating raw user text.", "Do not use same-origin behavior as a substitute for server authorization."],
         language="javascript", runnable=False,
         code='''const searchTerm = document.querySelector("#case-search").value.trim();
if (searchTerm.length > 80) throw new RangeError("Search term is too long");
const target = new URL("/cases", window.location.origin);
target.searchParams.set("term", searchTerm);
window.location.assign(target.pathname + target.search);''',
         related=["html/anchors-and-paths", "html/forms-get-post", "javascript/javascript-tutorial", "web-tech/http-request-response-contract"]),
    dict(path="web-tech/browser-parse-load-and-render", section=sections[0][0],
         title="Page loading: keep content available while CSS and scripts arrive",
         summary="Separate parsed HTML, styles, deferred behavior, and optional images.",
         definition="A browser can start building the document tree while HTML bytes arrive. Styles contribute to the layout and paint decision, while scripts can modify the tree and may pause parsing when loaded synchronously in the wrong place. The critical path is a dependency graph, not a single download timer. A page should send useful text and navigation in HTML, reserve stable dimensions for an important image, and load behavior after the parser can see the controls it will enhance. A deferred script runs after HTML parsing and preserves order among similarly deferred scripts; an asynchronous script is better suited to work that does not depend on document order. This lesson treats JavaScript as an enhancement to a readable case record rather than the sole carrier of its content.",
         case="A case page shows the title, status, and record body before any enhancement runs. Its stylesheet can establish the layout, and a deferred local script adds a copy control after the document is parsed. An image of equipment declares width and height so surrounding copy does not jump when pixels arrive. If the script fails, readers still get the case facts and links. If CSS fails, the document's semantic order still makes sense. The browser may choose a different image resource at a different viewport width, but the visible purpose and text alternative stay the same.",
         cost="Parsing work grows with document and stylesheet size; script execution adds main-thread work that can delay interaction. The example has one stylesheet and one deferred script, but a real page's transfer budget includes fonts, images, and third-party code. Width and height reserve layout space but do not make a large image cheap to download. Measure the rendered page at real viewports and input conditions before adding resource hints or more scripts. The complexity of an interaction handler is separate from the browser's parsing and painting costs.",
         mistakes=["Do not make the script download the only copy of essential case text.", "Do not use async for a script that depends on earlier scripts executing first.", "Do not omit image dimensions when the page can reserve a stable box.", "Do not describe a fast network response as proof of a fast rendered page."],
         language="html", runnable=False,
         code='''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Case 47 | AI Trove</title>
  <link rel="stylesheet" href="/assets/case.css">
  <script src="/assets/case-actions.js" defer></script>
</head>
<body>
  <main>
    <h1>Pump inspection, case 47</h1>
    <p>Status: review pending</p>
    <img src="/assets/pump-47.webp" width="640" height="360" alt="Pump 47 beside its inspection label">
    <p>The service valve was checked at 08:30.</p>
  </main>
</body>
</html>''',
         related=["html/document-skeleton", "html/script-loading", "html/responsive-images", "css/responsive-layout"]),
    dict(path="web-tech/dom-events-progressive-enhancement", section=sections[1][0],
         title="DOM events: enhance a working control without losing its baseline",
         summary="Attach one handler to a form that already submits a useful request.",
         definition="An event handler is an optional layer over an existing interaction contract. A search form with a real action, method, label, and submit button works through browser navigation before JavaScript is available. A script can listen for submit and offer faster in-page results, but it should cancel default submission only when it is ready to perform the replacement path. Event delegation can attach one listener to a stable parent when child controls are inserted later; it still needs a precise target check. Here the handler sends an enhanced read request and falls back to native navigation if that request fails. The form also works if enhancement never initializes.",
         case="An incident analyst types 'pump 47' and submits. The browser can issue a GET search through the form action. Once the script has attached, the handler fetches a count and reports it in an existing status region. A failed request invokes the form's normal navigation path. The script uses textContent rather than inserting untrusted HTML. Pressing Enter in the input and activating the button both use the same submit event. A click-only handler on the button would miss the keyboard path and could fail when another submit control is added.",
         cost="The handler performs direct DOM lookups at initialization and O(L) query construction per submit, where L is the encoded term length. Delegating a large table of controls to one parent can reduce listener count from O(N) to O(1), but target matching still occurs on each event. Network latency and JSON parsing dominate this small handler. The status node remains stable instead of rebuilding the whole page. A full results view would also need an empty state and a way to prevent an older response from overwriting a newer one.",
         mistakes=["Do not make a button click the only path for form submission.", "Do not call preventDefault before an enhanced path can handle the task.", "Do not place untrusted search text into innerHTML.", "Do not remove the form action merely because JavaScript is expected to run."],
         language="html", runnable=False,
         code='''<form id="case-search-form" action="/cases" method="get">
  <label for="case-search-term">Case terms</label>
  <input id="case-search-term" name="term" required maxlength="80">
  <button type="submit">Search cases</button>
</form>
<p id="case-search-status" role="status"></p>
<script>
  const searchForm = document.querySelector("#case-search-form");
  const searchStatus = document.querySelector("#case-search-status");
  searchForm.addEventListener("submit", async (event) => {
    const searchTerm = searchForm.elements.term.value.trim();
    if (!searchTerm) return;
    event.preventDefault();
    searchStatus.textContent = `Searching for ${searchTerm}`;
    try {
      const query = new URLSearchParams({ term: searchTerm });
      const response = await fetch(`/cases?${query}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      searchStatus.textContent = `${result.total} cases found`;
    } catch {
      searchForm.submit();
    }
  });
</script>''',
         related=["html/forms-get-post", "html/form-labels", "html/live-status", "javascript/javascript-tutorial"]),
    dict(path="web-tech/fetch-status-and-abort", section=sections[1][0],
         title="Fetch requests: separate HTTP failure, transport failure, and cancellation",
         summary="Check response status, bound waiting time, and discard obsolete results.",
         definition="Fetch resolves when response headers arrive, including responses with error status codes. A caller must inspect response.ok or status before decoding a success body. A network failure rejects the promise; cancellation through AbortController also rejects, but is an expected outcome when a newer search replaces an older one. The user interface should not show a stale result from an earlier request after a newer query starts. One controller per in-flight search lets the next request abort the previous one. A timeout is a policy decision, not proof that the server did no work; a mutation may have completed even when the client stopped waiting. The example is a browser module for a read-only case search.",
         case="An analyst searches for pump, then quickly searches for valve. The valve request cancels the pump request and becomes the only result allowed to update the list. A 404 response produces a missing-result state instead of pretending JSON parsing failed. A 500 response is classified as an HTTP server error, while an offline failure has no response status. The code sets textContent for one summary field; it does not put a returned HTML fragment directly into the page. If the search endpoint changes state, cancellation and retries require a stronger server contract than this read-only example.",
         cost="For each search, request and response transfer dominate local controller setup, which is O(1). Decoding a JSON payload of B bytes costs O(B) time and storage. Aborting an obsolete fetch may save browser work but does not guarantee that the server stopped processing. A new request can still race with state changes unless the UI checks which query owns the display. The helper here uses a monotonically increasing request number in addition to aborting, so only the latest invocation can publish its summary.",
         mistakes=["Do not treat a resolved fetch promise as proof of HTTP success.", "Do not display an older response after a newer query owns the view.", "Do not report an intentional abort as a server outage.", "Do not retry a state-changing request merely because the browser timeout fired."],
         language="javascript", runnable=False,
         code='''let activeSearch;
let requestNumber = 0;
async function searchCases(term, statusNode) {
  activeSearch?.abort();
  const controller = new AbortController();
  activeSearch = controller;
  const owner = ++requestNumber;
  const timeout = setTimeout(() => controller.abort(), 6000);
  try {
    const query = new URLSearchParams({ term });
    const response = await fetch(`/cases?${query}`, { signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (owner === requestNumber) statusNode.textContent = `${payload.total} cases`;
  } catch (error) {
    if (error.name !== "AbortError" && owner === requestNumber) {
      statusNode.textContent = "Search unavailable. Try again.";
    }
  } finally {
    clearTimeout(timeout);
  }
}''',
         related=["javascript/javascript-tutorial", "html/live-status", "web-tech/dom-events-progressive-enhancement", "web-tech/http-request-response-contract"]),
    dict(path="web-tech/form-server-validation", section=sections[1][0],
         title="Form submission: validate on the server and return field errors",
         summary="Preserve submitted values while rejecting records that break the stored contract.",
         definition="Browser validation helps users correct mistakes before a request, but the server owns the stored-data contract. A client can omit required controls, change hidden values, or call the endpoint directly. A server must parse within size limits, validate each field, authorize the operation, and return errors that can be attached to named controls. The example accepts a case number and a short inspection note. It returns a field-error object without mutating the record map when either field is invalid. The browser page should render an overall error summary and retain safe submitted values, allowing correction rather than forcing re-entry. This lesson separates syntax validation from permission checks; passing one does not imply the other.",
         case="A report for case 47 with an empty note returns status 422 and an error keyed to note. A report for case 47 with 'seal replaced' returns status 201 and stores that text. A caller who supplies a negative case number is rejected before storage. A hidden case number in a form is still caller-controlled and must be checked against the authorized case on the server. If a write succeeds but the response is lost, a blind retry might duplicate a side effect; a durable idempotency contract is separate from the field checks shown here.",
         cost="Validation scans the note once, taking O(L) time for note length L. The sample in-memory map uses expected O(1) lookup and update, with O(N) stored records. Parsing an unbounded body would break the stated cost and memory model, so a real server needs a request-size cap before decoding. Returning every field error in one response can reduce repeated round trips compared with revealing only one error at a time. Escaping is required when safe values and messages are rendered back into HTML; server validation does not sanitize arbitrary output contexts automatically.",
         mistakes=["Do not trust client-side required attributes as the only validation layer.", "Do not trust a hidden case ID as authorization evidence.", "Do not discard safe submitted values after a 422 response.", "Do not retry an ambiguous write without an idempotency or reconciliation rule."],
         language="javascript", runnable=True,
         code='''const inspections = new Map();
function saveInspection(input) {
  const errors = {};
  if (!Number.isInteger(input.caseId) || input.caseId < 1) {
    errors.caseId = "Choose a valid case";
  }
  if (typeof input.note !== "string" || !input.note.trim() || input.note.length > 160) {
    errors.note = "Write a note of at most 160 characters";
  }
  if (Object.keys(errors).length) return { status: 422, errors };
  const note = input.note.trim();
  inspections.set(input.caseId, note);
  return { status: 201, caseId: input.caseId };
}
console.log(saveInspection({ caseId: 47, note: " " }).status);
console.log(saveInspection({ caseId: 47, note: "seal replaced" }).status);
console.log(inspections.get(47));''',
         related=["html/form-validation", "html/form-help-and-errors", "html/forms-get-post", "web-tech/http-request-response-contract"]),
    dict(path="web-tech/session-cookie-and-csrf-boundary", section=sections[2][0],
         title="Sessions and CSRF: keep identity on the server",
         summary="Model a session cookie and a separate write token without trusting browser storage.",
         definition="A session identifier is an opaque reference to server-side state. After authentication, a server can issue it in a cookie marked HttpOnly and Secure, with a SameSite policy suited to the flow. HttpOnly limits script access to the cookie; it does not stop the browser from sending the cookie with an eligible request. That automatic sending is why a state-changing endpoint needs a cross-site request forgery defense. A server-issued token bound to the active session can be checked on writes, alongside appropriate origin checks. SameSite is useful defense in depth, not a complete replacement for the write check. The model below generates unpredictable session and token values and compares the submitted token only after finding the session.",
         case="A reviewer is signed in and opens an inspection form. The server associates a fresh anti-forgery token with the session and includes it in that form. A write carrying the session cookie but no valid token is rejected before any record changes. Signing out invalidates the server-side session; merely deleting a browser display flag would not. In production, cookie scope, expiration, rotation, transport security, and login rate limits belong to the authentication design. This code demonstrates one boundary rather than a full login service.",
         cost="Map lookup is expected O(1), while comparing fixed-size token buffers is O(K) for token byte length K. Keeping active sessions consumes O(S) memory or equivalent durable storage for S sessions. Random generation has a small fixed cost per session. A distributed service needs shared session state or a deliberate stateless design; copying a session map to every process would make sign-out inconsistent. Never log the raw cookie or token to troubleshoot failures. A forged request can arrive even when the user has not opened your form, so the server must own this check.",
         mistakes=["Do not keep bearer session identifiers in localStorage for convenience.", "Do not treat SameSite alone as a complete write defense.", "Do not compare a token before verifying its session exists.", "Do not confuse a CSRF token with authorization to edit a particular record."],
         language="javascript", runnable=True,
         code='''const { randomBytes, timingSafeEqual } = require("node:crypto");
const sessions = new Map();
const sessionId = randomBytes(24).toString("hex");
const writeToken = randomBytes(24).toString("hex");
sessions.set(sessionId, { reviewerId: 47, writeToken });
function mayWrite(cookieSessionId, submittedToken) {
  const session = sessions.get(cookieSessionId);
  if (!session || typeof submittedToken !== "string") return false;
  const expected = Buffer.from(session.writeToken, "hex");
  const supplied = Buffer.from(submittedToken, "hex");
  return expected.length === supplied.length && timingSafeEqual(expected, supplied);
}
console.log(mayWrite(sessionId, writeToken));
console.log(mayWrite(sessionId, "invalid"));''',
         related=["web-tech/form-server-validation", "web-tech/browser-storage-boundary", "web-tech/url-origin-and-query-boundary"]),
    dict(path="web-tech/browser-storage-boundary", section=sections[2][0],
         title="Browser storage: save convenience data without storing credentials",
         summary="Treat local storage as untrusted, optional, and visible to page scripts.",
         definition="Browser storage can preserve small interface preferences and draft text across page visits. It is not a secure vault: scripts running in the page's origin can read localStorage, users can edit it, and storage can be unavailable or cleared. A server should never use a value retrieved from localStorage as proof of identity or permission. The code below stores a display density choice with an explicit allowlist and a versioned key. Reading the value is wrapped in a try block because access and parsing can fail. Sensitive session credentials belong in a different design with server-side controls; a theme preference does not.",
         case="An analyst chooses compact rows for an inspection queue. The page writes 'compact' under a versioned preference key and restores it on the next visit. If storage is blocked, the queue stays readable using the default comfortable layout. If an attacker or old script writes an unknown string, the allowlist rejects it. A different browser profile will not inherit the choice, which is acceptable for a display preference but would be unacceptable for a shared workflow state. Draft submissions that matter should be saved with a server contract, conflict rules, and an explicit retention policy.",
         cost="A single preference read and write are small synchronous operations, but localStorage can block the main thread and should not hold large documents. The allowlist check is O(1); reading a value of length L and copying it is O(L). Storage quota, eviction, and private mode behavior vary, so failure must leave the interface usable. If a value must be shared among devices or audited, server storage is the appropriate authority. A storage event can notify other tabs, but it does not turn local data into trusted state.",
         mistakes=["Do not store passwords or bearer tokens beside interface preferences.", "Do not assume localStorage always exists or accepts writes.", "Do not trust a restored value without checking its allowed shape.", "Do not treat one browser profile as the source of truth for team data."],
         language="javascript", runnable=False,
         code='''const preferenceKey = "inspection-density-v2";
const allowedDensity = new Set(["compact", "comfortable"]);
function readDensity() {
  try {
    const saved = localStorage.getItem(preferenceKey);
    return allowedDensity.has(saved) ? saved : "comfortable";
  } catch {
    return "comfortable";
  }
}
function saveDensity(selection) {
  if (!allowedDensity.has(selection)) return false;
  try {
    localStorage.setItem(preferenceKey, selection);
    return true;
  } catch {
    return false;
  }
}''',
         related=["web-tech/session-cookie-and-csrf-boundary", "web-tech/cache-etag-revalidation", "javascript/javascript-tutorial"]),
    dict(path="web-tech/cache-etag-revalidation", section=sections[2][0],
         title="HTTP caching: validate a changed representation with an ETag",
         summary="Return 304 only when the client's validator matches the current representation.",
         definition="Caching is a contract about freshness and reuse, not an instruction to store every response forever. A server can attach an entity tag to a representation. On a later read, the client can send If-None-Match; a matching current tag lets the server return 304 without sending that representation body. A changed representation needs a new tag and a normal response body. Cache-Control sets the reuse policy and is especially important for personalized data. The compact model below hashes the exact text used as the representation and compares a supplied validator. A real HTTP implementation must also handle weak validators, content negotiation, authentication, and the correct response headers.",
         case="A public maintenance notice first contains 'Valve review pending'. The client stores its tag. The next read supplies the same tag and gets 304 with no body. After the notice changes to 'Valve review complete', its tag differs and the client receives 200 with the new text. A personalized inspection queue should use a privacy-aware cache policy rather than being treated like a public notice. A 304 is meaningful only when the client already has a reusable representation; it is not a substitute for the first response.",
         cost="Hashing a representation of B bytes is O(B) time; storing the current notice is O(B) space. Comparing fixed-length tags is O(1) after the tag is computed. A 304 can save roughly B response-body bytes, though headers and request latency remain. Computing a hash on every request may itself be expensive for a large generated page; a service can cache a version token when the underlying content changes. A CDN or shared cache also needs correct variation and privacy rules so one user's body never appears in another user's response.",
         mistakes=["Do not send 304 if the representation changed.", "Do not give a public shared cache a private user's page without a safe policy.", "Do not assume a validator removes request latency.", "Do not vary the body by language or authorization while reusing one tag carelessly."],
         language="javascript", runnable=True,
         code='''const { createHash } = require("node:crypto");
function serveNotice(text, ifNoneMatch) {
  const etag = `"${createHash("sha256").update(text).digest("hex")}"`;
  if (ifNoneMatch === etag) return { status: 304, etag, body: null };
  return { status: 200, etag, body: text };
}
const first = serveNotice("Valve review pending");
const unchanged = serveNotice("Valve review pending", first.etag);
const changed = serveNotice("Valve review complete", first.etag);
console.log(first.status, unchanged.status, changed.status);
console.log(unchanged.body === null, changed.body);''',
         related=["web-tech/http-request-response-contract", "web-tech/browser-parse-load-and-render", "web-tech/performance-budget-and-layout-stability"]),
    dict(path="web-tech/accessible-feedback-and-keyboard", section=sections[3][0],
         title="Accessible forms: connect labels, errors, and focus",
         summary="Make a failed submission understandable without relying on color or pointer input.",
         definition="A form error needs to identify the field, state what failed, and offer a way to correct it. A visible label gives a control its name; help and error text can be associated using aria-describedby, and aria-invalid marks a field after validation fails. An error summary can collect failures and receive focus after a server response so a keyboard user knows what happened. A status message can announce a successful save without moving focus. These features support the form's actual behavior; they cannot repair missing labels or a disabled submit path. The static markup below shows a server-rendered invalid state. A successful initial render should omit the error state until there is an error.",
         case="An inspector submits case 47 with an empty note. The server returns the form, preserves case 47, and renders an error summary. Focus moves to that summary; its link points to the note control. The field has a persistent label, a length hint, an error message, and aria-invalid. The user can tab to the note and correct it. Red text alone would fail a user who cannot distinguish that color, and a toast that disappears before screen-reader announcement could hide the only explanation. The summary should include every invalid field on a longer form.",
         cost="Rendering one error per invalid field takes O(F) time and DOM nodes for F fields. Associating nodes by ID is a constant-size markup cost per field. A client-side validator that traverses all controls also takes O(F), but the server still validates the submitted payload. Accessibility checks require keyboard use and assistive-technology testing, not only inspection of attributes. Moving focus on every keystroke would be disruptive; focus the summary once after the failed submission is rendered. Keep the error text in normal reading order and do not hide it behind a hover-only control.",
         mistakes=["Do not use placeholder text as the only field label.", "Do not report an error only through color or an icon.", "Do not set aria-invalid without explaining how to fix the value.", "Do not move focus repeatedly while the user is editing a field."],
         language="html", runnable=False,
         code='''<main>
  <h1>Record inspection</h1>
  <div id="error-summary" tabindex="-1" role="alert">
    <h2>Check the inspection note</h2>
    <p><a href="#inspection-note">Enter a note before saving.</a></p>
  </div>
  <form action="/inspections" method="post">
    <label for="inspection-note">Inspection note</label>
    <p id="note-help">Describe the work in 160 characters or fewer.</p>
    <p id="note-error">A note is required.</p>
    <textarea id="inspection-note" name="note" maxlength="160"
      aria-describedby="note-help note-error" aria-invalid="true"></textarea>
    <button type="submit">Save inspection</button>
  </form>
</main>
<script>document.querySelector("#error-summary").focus();</script>''',
         related=["html/form-labels", "html/form-help-and-errors", "html/live-status", "web-tech/form-server-validation"]),
    dict(path="web-tech/performance-budget-and-layout-stability", section=sections[3][0],
         title="Page performance: budget the critical path and reserve layout space",
         summary="Measure loading, interaction, and visual stability as separate user costs.",
         definition="A page can return HTML quickly yet feel slow because a large image, blocking script, expensive layout, or long interaction handler delays what the user sees and does. The useful budget covers the critical content, the work needed for a response to input, and shifts of visible elements after they appear. Reserve dimensions for media, keep essential text in HTML, defer optional behavior, and avoid loading an entire toolset for one button. Measurements should include a cold mobile load and a realistic interaction, then point to the actual expensive resource or task. The markup below declares a stable image box and keeps the case summary ahead of optional details. It is a starting contract, not a performance score.",
         case="An inspection dashboard previously inserted a large chart above the case title only after data arrived. The title moved down as the user tried to tap it. A reserved chart box keeps the layout steady, while a compact case summary remains readable without waiting for the chart. A measured slow interaction may still come from script work after a click; image dimensions will not fix that. Similarly, compressing one image cannot solve a server delay. The team should change the bottleneck shown in measurements and then remeasure under the same conditions.",
         cost="An image of B transferred bytes has O(B) transfer and decode input, but decode memory can be far larger than compressed size. A client-side handler that scans N rows per input event has O(N) work each time and may make typing feel delayed. Reserving width and height costs almost no runtime work but can prevent a late box resize. Smaller assets can save bytes, while fewer synchronous tasks can improve interaction. Performance work is empirical: set a page-specific budget, record the baseline, change one cause, and compare the same route and device class.",
         mistakes=["Do not call a page fast solely because the server responds quickly.", "Do not omit media dimensions and let important controls shift after load.", "Do not lazy-load the first meaningful image without measuring the effect.", "Do not ship a large script bundle for a minor control without checking its interaction cost."],
         language="html", runnable=False,
         code='''<main>
  <h1>Case 47: inspection queue</h1>
  <p>Three checks are waiting for review.</p>
  <figure>
    <img src="/assets/queue-chart.webp" width="720" height="360"
      alt="Queue chart: three waiting checks and five complete checks">
    <figcaption>Queue at the last recorded update.</figcaption>
  </figure>
  <p><a href="/cases/47">Open the case record</a></p>
</main>
<script src="/assets/queue-filters.js" defer></script>''',
         related=["web-tech/browser-parse-load-and-render", "web-tech/cache-etag-revalidation", "html/responsive-images", "css/responsive-layout"]),
    dict(path="web-tech/release-smoke-and-rollback", section=sections[3][0],
         title="Release checks: prove the critical route and prepare a rollback",
         summary="Check a public page and API contract after deployment, then stop on evidence of regression.",
         definition="A successful build proves that files were produced, not that the deployed service works for users. A small post-release smoke check should request the critical page and API, verify expected status and content type, and assert that the page contains a stable landmark. A separate write check needs safe test data and cleanup; do not submit a real customer action from an unattended probe. If a critical check fails, the release procedure should stop traffic growth and restore the previously known working version. A rollback plan should identify the version, data compatibility, and operator action before deployment begins. The Node script below checks read-only contracts against a base location supplied at run time.",
         case="A case portal build passes locally, but deployment points the case API to the wrong route. The home page responds 200, while the case endpoint responds 404. A post-release check catches the mismatch before the rollout expands. The operator restores the prior application version and investigates the route mapping. If the new release also changed stored data in a way the prior version cannot read, a code rollback alone is insufficient; migration and compatibility planning have to precede the release. The check is deliberately read-only and makes no claim about every user journey.",
         cost="Two network reads take O(R) time for response bytes R plus network latency, and this script retains O(R) response text for the page. More probes improve coverage but increase deploy time and can create load. Keep the first gate small, deterministic, and tied to the most important path; run broader end-to-end checks in a separate stage. A 200 response can still contain the wrong page, which is why the script checks a landmark as well as status. Monitor errors after rollout because a point-in-time smoke check cannot detect later failures or traffic-specific bugs.",
         mistakes=["Do not treat a green build as proof that deployment routes are correct.", "Do not let a smoke test perform a real customer write without safe isolation.", "Do not assume code rollback reverses an incompatible data migration.", "Do not check only status 200 when the response may be the wrong page."],
         language="javascript", runnable=False,
         code='''async function verifyRelease(baseLocation) {
  const pageTarget = new URL("/cases/47", baseLocation);
  const apiTarget = new URL("/api/cases/47", baseLocation);
  const [page, api] = await Promise.all([fetch(pageTarget), fetch(apiTarget)]);
  if (page.status !== 200 || api.status !== 200) {
    throw new Error(`Route failure: page ${page.status}, API ${api.status}`);
  }
  if (!page.headers.get("content-type")?.includes("text/html")) {
    throw new Error("Case page returned the wrong content type");
  }
  const markup = await page.text();
  if (!markup.includes("Case 47")) throw new Error("Case landmark is missing");
  return true;
}
const baseLocation = process.env.RELEASE_BASE_LOCATION;
if (!baseLocation) throw new Error("Set RELEASE_BASE_LOCATION");
verifyRelease(baseLocation).then(() => console.log("Read paths verified"));''',
         related=["web-tech/http-request-response-contract", "web-tech/performance-budget-and-layout-stability", "devops/devops-tutorial"]),
]

lessons.extend([
    dict(path="web-tech/dns-tls-and-first-connection", section=sections[0][0],
         title="First connection: separate name resolution, TLS, and HTTP",
         summary="Locate a service, protect the connection, then interpret its response.",
         definition="Opening a page crosses several boundaries before application code receives an HTTP request. A resolver maps the host name to an address; the client establishes a transport connection; TLS authenticates the server name and protects bytes in transit; only then does HTTP carry a method and target to the service. A DNS answer is not proof that the application route exists. A valid TLS connection is not proof that the user is authorized. Likewise, an HTTP 404 says the service answered but could not find the requested resource, which is different from a resolution or certificate failure. Keep these layers separate when debugging a page that will not open.",
         case="A case portal works on an internal machine but not from a reviewer laptop. If the name cannot resolve, no request reaches the portal. If the certificate does not match the name, the browser stops before accepting the HTTP response. If the connection succeeds and the portal returns 404 for case 47, the application route or record is the next place to inspect. A single 'site down' label hides the diagnostic difference. The small function classifies observations already collected by the client; it is not a replacement for measuring a real connection.",
         cost="The local classifier is O(1) time and space, but real name lookup, connection setup, and TLS negotiation add network round trips before application bytes arrive. Connection reuse can amortize setup for subsequent requests. Shortening the HTML body cannot repair a failing certificate or DNS record. Conversely, a successful resolution does not measure rendering. Record timings and errors at the boundary that produced them, and avoid logging sensitive request bodies merely to diagnose connection problems.",
         mistakes=["Do not describe a DNS failure as an application 404.", "Do not bypass a certificate error to make a production page load.", "Do not assume HTTPS alone grants application permission.", "Do not use one generic retry rule for every connection failure."],
         language="javascript", runnable=True,
         code='''function classifyVisit({ resolved, tlsTrusted, httpStatus }) {
  if (!resolved) return "name resolution failed";
  if (!tlsTrusted) return "TLS identity check failed";
  if (httpStatus === 404) return "application resource missing";
  if (httpStatus >= 500) return "application server error";
  return "HTTP response received";
}
console.log(classifyVisit({ resolved: true, tlsTrusted: true, httpStatus: 404 }));
console.log(classifyVisit({ resolved: true, tlsTrusted: false, httpStatus: null }));''',
         related=["web-tech/http-request-response-contract", "web-tech/url-origin-and-query-boundary", "web-tech/release-smoke-and-rollback"]),
    dict(path="web-tech/route-parameters-and-error-responses", section=sections[0][0],
         title="Routing: validate path parameters and return a stable error shape",
         summary="Distinguish a malformed case ID from an absent case and a forbidden one.",
         definition="A route pattern can capture a path segment, but the captured bytes remain untrusted text. Parse a case ID under a strict rule before asking storage for a record. A malformed identifier should not accidentally become a different valid number through permissive parsing. The route then decides whether the caller can read that specific case, queries storage, and returns a predictable response. The client needs a stable error shape to show a useful message without guessing from arbitrary prose. An unauthorized response must not reveal private record details; choose 403 or a deliberately concealed 404 policy consistently. The example keeps parsing, permission, and lookup as separate checks.",
         case="A reviewer requests case 47 and receives the record. The path '/cases/47extra' is malformed and returns 400, not case 47. A valid but absent case 83 returns 404. A case outside the reviewer's assignment returns 403 in this model, without including the private title. The server's ordering is deliberate: a strict path parser prevents accidental coercion, then authorization decides whether a valid identifier may be read. A larger service should make the concealment policy explicit if it does not wish to reveal which IDs exist.",
         cost="Parsing an ID string of length L takes O(L) time. The membership checks use expected O(1) time and O(N) storage for N case assignments and records. A database-backed route has additional query cost and must avoid fetching or serializing sensitive fields before authorization. A stable error object adds a few bytes but avoids brittle client text matching. Keep error detail safe for the recipient while retaining richer diagnostic context in protected server logs.",
         mistakes=["Do not use parseInt on a path and silently accept a trailing suffix.", "Do not serialize a private case before checking permission.", "Do not make clients infer error type from free-form prose.", "Do not reveal a forbidden record title inside an error body."],
         language="javascript", runnable=True,
         code='''const cases = new Map([[47, { title: "Pump inspection" }]]);
const assignedCaseIds = new Set([47, 83]);
function readCase(rawId) {
  if (!/^[1-9][0-9]*$/.test(rawId)) return { status: 400, code: "invalid_case_id" };
  const caseId = Number(rawId);
  if (!Number.isSafeInteger(caseId)) return { status: 400, code: "invalid_case_id" };
  if (!assignedCaseIds.has(caseId)) return { status: 403, code: "forbidden" };
  const record = cases.get(caseId);
  return record ? { status: 200, record } : { status: 404, code: "not_found" };
}
console.log(readCase("47").status);
console.log(readCase("47extra").code);
console.log(readCase("83").status);''',
         related=["web-tech/http-request-response-contract", "web-tech/form-server-validation", "web-tech/session-cookie-and-csrf-boundary"]),
    dict(path="web-tech/cors-and-cross-origin-requests", section=sections[1][0],
         title="Cross-origin requests: read CORS as a browser access policy",
         summary="Allow only intended browser origins without mistaking CORS for authentication.",
         definition="A page's origin includes scheme, host, and port. When a script requests another origin, the browser applies the cross-origin access rules to decide whether that script may read the response. The server communicates allowed origins through response headers, and some request shapes trigger a preflight check before the actual request. This browser policy does not authenticate the caller: a non-browser client can send a request without obeying it. An endpoint still needs its ordinary session, token, authorization, and input checks. For credentialed browser requests, the server must name an allowed origin rather than use a wildcard, and the client must opt into sending credentials when needed. The example uses a fixed origin allowlist and refuses unknown origins.",
         case="An internal dashboard hosted on one origin reads a case API hosted on another. The API permits only the dashboard origin, so a browser script from an unrelated page cannot read its response. That unrelated page may still attempt a request, and a direct command-line client is unaffected by browser CORS rules; neither fact grants access to private case data. A reviewer session and case-level permission remain necessary. A preflight failure appears in browser developer tools before application code receives the intended response, while a server-side 403 is a separate authorization result.",
         cost="Checking membership in a small allowlist is expected O(1) with a set. A preflight can add a network round trip, although suitable caching may reduce repeated checks. Reflecting arbitrary Origin values without an allowlist is a policy error, not a performance optimization. If responses vary by Origin, caches must preserve that variation to avoid serving incorrect access headers. The example returns only header decisions; a real server must apply them consistently to both preflight and actual responses without using CORS as a substitute for permission checks.",
         mistakes=["Do not use Access-Control-Allow-Origin wildcard with credentialed browser access.", "Do not treat CORS as authentication or record authorization.", "Do not reflect any caller-supplied Origin without a policy.", "Do not diagnose every blocked browser read as an API 500."],
         language="javascript", runnable=True,
         code='''const allowedOrigins = new Set(["https://review.aitrove.test"]);
function accessHeaders(origin) {
  if (!allowedOrigins.has(origin)) return {};
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Credentials": "true",
    Vary: "Origin"
  };
}
console.log(Object.keys(accessHeaders("https://review.aitrove.test")).length);
console.log(Object.keys(accessHeaders("https://unknown.aitrove.test")).length);''',
         related=["web-tech/url-origin-and-query-boundary", "web-tech/session-cookie-and-csrf-boundary", "web-tech/fetch-status-and-abort"]),
    dict(path="web-tech/responsive-interaction-contract", section=sections[1][0],
         title="Responsive interaction: preserve content and control order",
         summary="Change layout across widths without hiding the only path to an action.",
         definition="Responsive layout is more than fitting boxes into a narrow viewport. The reading order, keyboard order, labels, and primary action must still make sense when columns collapse. Start with semantic HTML in the order a person should read it, then use CSS to place regions side by side when space allows. The DOM order remains the accessibility and keyboard baseline even if CSS paints elements elsewhere. Avoid a mobile menu that contains the only route to a case when its script fails. The snippet uses a simple grid that becomes two columns only when width allows, while the form and case details remain in one continuous document order.",
         case="An inspector opens case 47 on a phone. The case summary appears before the update form, matching the desktop reading order. At a wide viewport, CSS places the two sections side by side; it does not move the form ahead of the summary in the DOM. The submit button remains visible and usable through touch, keyboard, and script-free form submission. A fixed-width panel would force horizontal scrolling, while using CSS order to visually reverse controls could confuse a keyboard user whose focus still follows document order.",
         cost="CSS grid layout cost grows with the number and complexity of elements being laid out, not just the media query count. This example has two regions, so the layout work is small; a page with hundreds of cards should inspect style and layout timing rather than assume a breakpoint is the bottleneck. A second mobile-only DOM copy doubles content and can create duplicate IDs or inconsistent form state. Keep one semantic source and test narrow, wide, zoomed, and keyboard views. CSS cannot repair a control missing from HTML.",
         mistakes=["Do not visually reverse controls while leaving a contradictory keyboard order.", "Do not duplicate the whole form for a mobile breakpoint.", "Do not make a script-only menu the sole path to an important page.", "Do not solve overflow by clipping essential text or controls."],
         language="html", runnable=False,
         code='''<main class="case-layout">
  <section aria-labelledby="case-title">
    <h1 id="case-title">Case 47</h1>
    <p>The service valve needs a second review.</p>
  </section>
  <form action="/inspections" method="post">
    <label for="review-note">Inspection note</label>
    <textarea id="review-note" name="note" required></textarea>
    <button type="submit">Save note</button>
  </form>
</main>
<style>
  .case-layout { display: grid; gap: 1.5rem; }
  @media (min-width: 52rem) {
    .case-layout { grid-template-columns: minmax(0, 2fr) minmax(16rem, 1fr); }
  }
</style>''',
         related=["css/responsive-layout", "html/forms-get-post", "web-tech/accessible-feedback-and-keyboard"]),
    dict(path="web-tech/output-escaping-and-csp", section=sections[2][0],
         title="Untrusted output: escape by context and constrain scripts",
         summary="Keep user text as text, then add a script policy as another boundary.",
         definition="A user-submitted inspection note is data, even if it contains angle brackets or script-looking text. Rendering it with innerHTML asks the browser to parse it as markup. Rendering it with textContent keeps those bytes as text. Server-rendered templates must also escape values for their specific output context; HTML text, attributes, URLs, and script literals do not share one universal escaping rule. A Content Security Policy can limit which scripts execute, but it is defense in depth rather than permission to insert unsafe HTML. The browser example below creates a note element and assigns textContent. It also avoids constructing a link from unchecked input. Rich text needs a deliberately designed sanitizer and supported markup policy.",
         case="A submitted note contains '<img src=x onerror=alert(1)>'. On a case page it should appear as the literal note, not create an image element or run code. The DOM code places it inside a paragraph as text. If the same value is inserted into a server template's attribute, it must be escaped for an attribute context instead. A strict script policy can reduce the impact of some injection mistakes, but a policy that allows unsafe inline script defeats much of that protection. Review both the data path and the script policy rather than declaring either alone sufficient.",
         cost="Assigning textContent copies O(L) characters for note length L and creates one DOM node. Sanitizing allowed rich text has greater parsing and maintenance cost and should be chosen only if the product needs rich text. A restrictive script policy can require changes to inline scripts and third-party integrations, so start with an inventory and test the policy before enforcing it. Client-side escaping does not repair unsafe server-rendered templates or stored content already emitted in the wrong context. Keep the trust boundary explicit at every render point.",
         mistakes=["Do not put untrusted note text into innerHTML.", "Do not apply HTML-text escaping to a JavaScript or URL context and assume safety.", "Do not call a permissive script policy a complete injection defense.", "Do not build navigation targets from unchecked user strings."],
         language="javascript", runnable=False,
         code='''function showInspectionNote(noteText, notesList) {
  if (typeof noteText !== "string") throw new TypeError("Expected note text");
  const noteItem = document.createElement("li");
  noteItem.textContent = noteText;
  notesList.append(noteItem);
}
const notesList = document.querySelector("#inspection-notes");
showInspectionNote("<img src=x onerror=alert(1)>", notesList);''',
         related=["web-tech/form-server-validation", "web-tech/session-cookie-and-csrf-boundary", "html/document-skeleton"]),
    dict(path="web-tech/record-level-authorization", section=sections[2][0],
         title="Authorization: check permission for this record on every request",
         summary="Distinguish a signed-in identity from authority over case 47.",
         definition="Authentication identifies a caller; authorization decides whether that caller may perform this action on this resource. A valid session does not imply access to every case ID. The server must check the reviewer-to-case relationship on both reads and writes, including direct API requests that bypass navigation. A hidden form field or disabled control is not permission evidence. The example keeps an assignment set per reviewer and rejects a write before it modifies the record map. For a real database, the check and mutation may need a transaction or a conditional write so a permission change cannot race between a read and update.",
         case="Reviewer 29 is assigned to case 47, but not case 83. A POST for case 47 stores the note. A POST for case 83 returns 403 with no mutation, even if the reviewer edits the form field manually. If the reviewer loses the assignment while editing, the server must use the current permission at submit time rather than what the page displayed earlier. An administrator may have a broader role, but role alone still needs a resource policy. Audit logs should record the decision without copying sensitive note text unnecessarily.",
         cost="The in-memory assignment and record lookups are expected O(1); assignment storage is O(A) for A reviewer-case pairs. A database authorization join or indexed lookup has different costs and should be measured under realistic load. Combining the permission predicate with the write can prevent a time-of-check/time-of-use gap. Rechecking permission on every protected operation adds work, but caching permission without invalidation can leave revoked access active. Choose a policy whose revocation behavior is explicit.",
         mistakes=["Do not equate a valid session with permission on every record.", "Do not rely on a hidden case ID or disabled button for access control.", "Do not check a read route and forget the corresponding write route.", "Do not assume a stale page reflects current assignments."],
         language="javascript", runnable=True,
         code='''const assignments = new Map([[29, new Set([47])]]);
const inspectionNotes = new Map();
function writeNote(reviewerId, caseId, note) {
  if (!assignments.get(reviewerId)?.has(caseId)) {
    return { status: 403, code: "forbidden" };
  }
  if (typeof note !== "string" || !note.trim()) {
    return { status: 422, code: "note_required" };
  }
  inspectionNotes.set(caseId, note.trim());
  return { status: 200, code: "saved" };
}
console.log(writeNote(29, 83, "checked").status);
console.log(writeNote(29, 47, "seal checked").status);
console.log(inspectionNotes.has(83), inspectionNotes.get(47));''',
         related=["web-tech/session-cookie-and-csrf-boundary", "web-tech/route-parameters-and-error-responses", "web-tech/form-server-validation"]),
    dict(path="web-tech/contract-tests-across-boundaries", section=sections[3][0],
         title="Tests across boundaries: assert behavior, not implementation text",
         summary="Keep a small suite for route status, validation, and unauthorized mutation.",
         definition="A useful web test follows an observable contract: an input request, an expected response, and whether state changed. Unit tests can check a small parser or validator, while integration tests should exercise the route with its storage and authorization boundary. A browser test is valuable for keyboard flow and visible errors that a server unit test cannot see. Avoid tests that merely repeat the same condition in test code; they can pass while the actual endpoint wiring is broken. The Node assertions below test a compact handler's visible status and storage effects. A real project should run a smaller number of full-route tests with an isolated database and a browser check for the form.",
         case="A developer changes the case route so an unauthorized reviewer gets 200 with an empty body. A test that only looks for 'no exception' would pass; a contract test asserting 403 and no storage change catches the regression. A separate browser test submits the form by pressing Enter, follows the error summary, and confirms that safe input remains. One test per boundary gives clearer failure diagnosis than a giant test that loads the page, writes data, sends email, and checks a chart in one step. Fixtures should use distinct case IDs to avoid cross-test collisions.",
         cost="The sample tests run in O(T) assertions for T fixed cases and O(N) memory for the in-memory records. Integration tests add database and network setup cost; browser tests add startup and rendering time. Run fast deterministic checks on every change and the slower critical journey at appropriate gates. A fake can verify a pure policy, but it cannot prove the real route, cookie, or persistence wiring. Every test should state which boundary it covers and which failure it is meant to catch.",
         mistakes=["Do not assert only that a function returned without throwing.", "Do not mock the route layer in the only route contract test.", "Do not share mutable test data across cases without reset.", "Do not let a browser-only test replace focused server authorization checks."],
         language="javascript", runnable=True,
         code='''const assert = require("node:assert/strict");
const storedNotes = new Map();
function submitNote(assigned, caseId, note) {
  if (!assigned.has(caseId)) return { status: 403 };
  if (!note.trim()) return { status: 422 };
  storedNotes.set(caseId, note.trim());
  return { status: 201 };
}
assert.equal(submitNote(new Set([47]), 83, "checked").status, 403);
assert.equal(storedNotes.has(83), false);
assert.equal(submitNote(new Set([47]), 47, " ").status, 422);
assert.equal(submitNote(new Set([47]), 47, "seal checked").status, 201);
assert.equal(storedNotes.get(47), "seal checked");
console.log("4 boundary assertions passed");''',
         related=["web-tech/form-server-validation", "web-tech/record-level-authorization", "web-tech/release-smoke-and-rollback"]),
    dict(path="web-tech/observability-and-recovery", section=sections[3][0],
         title="Observability: connect user failure to a safe request trace",
         summary="Record status, route, duration, and a correlation ID without logging secrets.",
         definition="When a web request fails, the user needs a clear recovery path and the team needs enough context to find the server event. A correlation ID can connect a client-visible error to a protected server log entry. Logs should capture the route pattern, status, duration, and failure class; avoid raw session cookies, tokens, passwords, or unnecessary submitted notes. Aggregate rates and latency trends reveal problems that one smoke check misses. The example produces a structured event from known safe fields. A real service should generate or validate request IDs at its edge and pass them through downstream work, while keeping the full diagnostic trace behind access controls.",
         case="A reviewer sees 'Save unavailable' after submitting a note. The page includes request ID 'r-47-29' in the support detail, while the server log has the same ID, route pattern, 503 status, and 218-millisecond duration. The log omits the note and cookie. An operator can see that the case write route failed across many requests after a release, trigger rollback, and then inspect the underlying database error. A 422 validation error should not page an operator like a 503 outage; classification and aggregation matter as much as the log line itself.",
         cost="Writing one fixed-size event is O(1) application work and storage per request, but high traffic makes total log volume O(R) for R requests. Capturing full bodies would multiply storage and privacy risk; bounded fields are cheaper and safer. Histograms or rate counters add aggregation cost but make trends easier to spot. Sampling can reduce routine trace volume, yet security and error events may need a different retention rule. Measure alert quality: a noisy alert that no one trusts can hide the critical failure it was meant to expose.",
         mistakes=["Do not log session cookies or raw anti-forgery tokens.", "Do not make a 422 user correction look like a server outage.", "Do not expose internal exception details in a public error page.", "Do not rely on one successful smoke check as ongoing monitoring."],
         language="javascript", runnable=True,
         code='''function requestEvent({ requestId, route, status, durationMs }) {
  return { requestId, route, status, durationMs,
    failureClass: status >= 500 ? "server" : status >= 400 ? "client" : "none" };
}
const event = requestEvent({
  requestId: "r-47-29", route: "/cases/:caseId/notes", status: 503, durationMs: 218
});
console.log(JSON.stringify(event));''',
         related=["web-tech/release-smoke-and-rollback", "web-tech/contract-tests-across-boundaries", "devops/devops-tutorial"]),
])


def link(path, label=None):
    assert path in by_path, f"unresolved internal link: {path}"
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(label or by_path[path]["title"])}</a>'


def paragraphs(text):
    return "".join(f"<p>{html.escape(part.strip())}</p>" for part in text.split("\n\n") if part.strip())


def new_entry(path, title, summary, entry_type="article", section_path=None, kind="tutorial", sort_order=900):
    template = by_path["web-tech/getting-started"] if entry_type == "article" else by_path[subject_root]
    entry = copy.deepcopy(template)
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), type=entry_type,
                 path=path, title=title, summary=summary, category="Web Development",
                 subject="web-tech", difficulty="Intermediate" if entry_type == "article" else None,
                 tags=["web-tech", "web-development"], sort_order=sort_order,
                 status="published", created_at=stamp, updated_at=stamp, published_at=stamp,
                 body="")
    entry["data"] = {"subject_root": subject_root, "section_path": section_path or path,
                     "content_format": "html", "seo_ready": False}
    if entry_type == "article":
        entry["data"].update(kind=kind, author_path="authors/aitrove-editorial", reading_minutes=8)
    entries.append(entry)
    by_path[path] = entry
    return entry


for path, title, summary in sections:
    assert path not in by_path
    new_entry(path, title, summary, entry_type="subject")

for index, lesson in enumerate(lessons):
    assert lesson["path"] not in by_path
    new_entry(lesson["path"], lesson["title"], lesson["summary"],
              section_path=lesson["section"], sort_order=920 + index)

projects = [
    dict(path="web-tech/case-intake-end-to-end-project", title="Project: build a case intake path from form to stored record",
         summary="Specify the form, server contract, identity boundary, and failure path for an inspection record.",
         sections=[
             ("Define the contract", "Build a case intake form for case 47. The HTML must contain a visible label for the note, a real POST action, and a submit button. Specify a 160-character note limit, but enforce the same rule on the server; an attacker can bypass every browser control. A successful response should identify the created inspection, while an invalid note should return field errors and preserve safe input for correction. Decide whether a repeated POST may create another inspection or whether the client supplies an idempotency key. Write this contract down before adding a visual design."),
             ("Trace the boundaries", "Follow one submitted note through the browser, request, authentication check, authorization check, parsing, validation, persistence, and response. A cookie can identify a session, but the server must look it up and decide whether that reviewer may edit case 47. Include a CSRF defense for the write. Keep the case ID from a hidden field or path as untrusted input. If the note contains markup, escape it when rendering the confirmation. Store a timestamp on the server; do not accept the browser clock as an audit timestamp."),
             ("Verify failure and recovery", "Test an empty note, a 161-character note, a missing session, an unauthorized reviewer, a duplicate request, and a lost response after a committed write. For each, record expected status, whether storage changes, and the visible message. Submit with JavaScript disabled to confirm the native form still works. After adding an in-page enhancement, test keyboard submission and a network failure. The output of this project is a working path plus a short trace that proves which layer made each decision.")],
         code='''POST /inspections
Input: caseId=47, note="seal replaced", idempotencyKey="review-47-19"
Checks: session -> permission for case 47 -> CSRF token -> body limit -> fields
Success: 201, inspectionId=93
Invalid note: 422, errors.note="Write a note of at most 160 characters"
Repeated key: return the first committed result without a second write''',
         mistakes=["Do not trust the browser length limit as the storage rule.", "Do not infer record permission from a valid session alone.", "Do not blindly retry a write after an ambiguous response."],
         related=["web-tech/form-server-validation", "web-tech/session-cookie-and-csrf-boundary", "web-tech/accessible-feedback-and-keyboard", "web-tech/dom-events-progressive-enhancement"]),
    dict(path="web-tech/web-release-readiness-project", title="Project: ship a case page with measured release gates",
         summary="Build an accessible page, measure its cost, and prove the deployed read path.",
         sections=[
             ("Build the readable page", "Render the case title, status, and primary navigation in the initial HTML. Use a stable image box with useful alt text if a photograph conveys case information. Let a deferred script enhance one action while leaving the case record readable if that script fails. Keep request URLs relative to the application and distinguish a missing case from a failed connection. Establish a compact and wide layout that preserve reading order and keyboard focus order."),
             ("Measure the user cost", "Capture a baseline for the first meaningful content, image transfer size, layout movement, and response to an interaction on a mobile-sized viewport. Set a budget before changing code. If the image dominates transfer, resize or encode it for its displayed use. If a handler scans every case on each keypress, reduce that work or move it away from the input path. Repeat the same measurement after the change. Record the environment so the comparison is meaningful rather than presenting one score without context."),
             ("Release and rollback", "Create a read-only smoke check for the case page and its API. Verify status, content type, and a case-specific landmark. Run it immediately after deployment and stop rollout if it fails. Identify the previous application version and verify that it can still read the current stored data before the deploy. A migration that removes a field used by that version requires a compatibility stage. Record who can trigger rollback and what evidence starts it. Keep the release note focused on observed behavior and unresolved risk.")],
         code='''Release gate for case 47
Page: GET /cases/47 -> 200, text/html, heading includes "Case 47"
API: GET /api/cases/47 -> 200, expected JSON shape
Keyboard: primary action reachable and named
Visual: image dimensions reserve its layout box
Rollback: previous version can read current case record''',
         mistakes=["Do not equate a successful build with a working deployed route.", "Do not quote an unrepeatable performance number as a release result.", "Do not roll back code without checking data compatibility."],
         related=["web-tech/browser-parse-load-and-render", "web-tech/performance-budget-and-layout-stability", "web-tech/release-smoke-and-rollback", "css/responsive-layout"]),
]

for index, project in enumerate(projects):
    assert project["path"] not in by_path
    new_entry(project["path"], project["title"], project["summary"],
              section_path=project_hub, kind="project", sort_order=950 + index)

quiz_specs = [
    ("quizzes/web-development-browser-contracts", "Web Development: browser contracts quiz", [
        ("Which part of a URL is absent from the HTTP request target?", "The fragment", "The query", "The path", 0, "A fragment is handled by the browser after navigation; path and query participate in the request target."),
        ("What does fetch do for an HTTP 404 response?", "It resolves with a response to inspect", "It always rejects before headers", "It retries the request", 0, "HTTP error status is still a received response; code must check ok or status before treating its body as success."),
        ("Which form behavior should exist before enhancement code runs?", "A real action and method", "A button click listener only", "A hidden script-created input", 0, "The native form route provides a usable baseline when JavaScript is unavailable or the enhancement fails to load."),
        ("Why choose defer for a dependent page script?", "It waits for parsing and preserves order among deferred scripts", "It blocks every HTML token", "It runs before the document begins", 0, "A deferred script executes after parsing and keeps relative order with other deferred scripts, which suits DOM-dependent behavior."),
        ("What does a 201 response normally indicate in a create contract?", "A resource was created", "The request was only cached", "The resource does not exist", 0, "A create route should return a success status that matches the actual persisted result; failed validation must not claim creation."),
        ("What is the server's role when a browser field has required?", "Validate the submitted value again", "Trust the browser attribute", "Ignore all submitted fields", 0, "Clients can be modified or bypassed, so the server must enforce length, shape, permission, and other stored-data rules."),
        ("When can an older search response update the visible result?", "Only if it still owns the current query", "Whenever it arrives", "Only when it is larger", 0, "An earlier request may finish later than a newer one; ownership or sequence checking prevents stale display updates."),
        ("What does a URL query encoder protect?", "Data delimiters inside a value", "Server authorization", "Session secrecy", 0, "Encoding prevents input such as an ampersand from accidentally becoming a second parameter, but it grants no permission."),
        ("What is the right fallback if enhanced search fails?", "Use the form's native navigation path", "Erase the form action", "Silently discard input", 0, "A real GET action lets the browser complete the search even if in-page fetch or rendering fails."),
        ("What does an image width and height declaration mainly help?", "Reserve layout space", "Authenticate the image", "Make its bytes vanish", 0, "Dimensions let the browser allocate a stable box before pixels arrive; transfer and decode costs still remain."),
        ("Which response requires a different UI from a lost connection?", "A received 404", "An aborted request", "An offline failure", 0, "A received 404 says the server answered that the resource was missing, whereas transport failure has no HTTP status."),
        ("Why retain safe submitted values after validation fails?", "People can correct only the bad fields", "It bypasses authorization", "It changes GET into POST", 0, "Preserving safe values prevents unnecessary re-entry and lets an error summary point to the fields needing correction."),
    ]),
    ("quizzes/web-development-state-release-contracts", "Web Development: state and release quiz", [
        ("What should an opaque session cookie refer to?", "Server-side session state", "An editable client permission flag", "A query fragment", 0, "The server looks up the identifier and makes its own authorization decision; the client must not be the authority for permissions."),
        ("Why is a CSRF check needed on a cookie-authenticated write?", "The browser may send eligible cookies automatically", "The cookie makes every request safe", "The URL has no query", 0, "Automatic cookie sending can accompany a forged write; the server needs a separate write defense and permission checks."),
        ("What is a suitable localStorage value?", "A validated display preference", "A bearer session token", "An unreviewed permission level", 0, "Small convenience preferences can tolerate deletion and script access; credentials and authorization cannot."),
        ("When is a 304 response appropriate?", "The current representation matches the supplied validator", "A write was accepted", "The client has never fetched the resource", 0, "A matching validator lets a client reuse a body it already holds; changed content requires a new body."),
        ("What should a personalized page's cache policy consider?", "Whether a shared cache could expose another user's body", "Only the file extension", "Only image dimensions", 0, "A shared cache can mix user-specific representations without correct privacy and variation rules."),
        ("How should an invalid field be identified?", "Label, linked explanation, and invalid state", "Red color alone", "A disappearing icon only", 0, "A visible label and connected error text make the problem understandable without relying on color or a pointer."),
        ("Where should focus go after a full form rerender with errors?", "A focused error summary or first invalid field", "Nowhere by definition", "Always the page footer", 0, "A deliberate focus target alerts keyboard and assistive-technology users to the result of submission."),
        ("What does a fast HTML response fail to prove?", "That rendering and interaction are fast", "That the server sent bytes", "That a status exists", 0, "Images, styles, scripts, layout, and event work may still delay what the user sees or does after headers arrive."),
        ("What does a stable image box prevent?", "Late layout movement", "All network latency", "All script execution", 0, "Reserved dimensions reduce shifts as media loads, while transfer and main-thread work remain separate costs."),
        ("What must a post-release smoke check verify beyond status?", "Expected content type and a route-specific landmark", "Only the repository branch name", "Only the local build log", 0, "A route may return 200 with the wrong page; checking the representation makes the gate more meaningful."),
        ("Why might code rollback fail after a migration?", "The prior version cannot read the new data shape", "The prior version is always cached", "A fragment changed", 0, "Rollback needs data compatibility; removing a field used by the previous application can make the older binary fail."),
        ("What is the safe policy for ambiguous write retries?", "Use an idempotency or reconciliation contract", "Repeat immediately without a key", "Assume the server did nothing", 0, "A timeout does not prove the write failed; a stable key or state check avoids accidental duplicate effects."),
    ]),
]

for index, (path, title, questions) in enumerate(quiz_specs):
    assert path not in by_path
    quiz = new_entry(path, title, "Twelve explained questions covering the Web Development track.",
                     entry_type="quiz", section_path=quiz_hub, sort_order=980 + index)
    quiz["data"]["questions"] = []
    for question_index, (prompt, right, wrong_one, wrong_two, _, explanation) in enumerate(questions):
        options = [right, wrong_one, wrong_two]
        shift = question_index % 3
        options = options[shift:] + options[:shift]
        quiz["data"]["questions"].append({"prompt": prompt, "options": options,
                                             "answer": options.index(right), "explanation": explanation})

assert quiz_hub not in by_path
new_entry(quiz_hub, "Web Development: Quizzes", "Check browser, server, state, and release contracts.",
          entry_type="subject", sort_order=985)

for lesson in lessons:
    entry = by_path[lesson["path"]]
    code = html.escape(lesson["code"], quote=False)
    body = paragraphs(lesson["definition"])
    body += "<h2>Case study</h2>" + paragraphs(lesson["case"])
    body += f'<h2>Working contract</h2><pre><code class="language-{lesson["language"]}">{code}</code></pre>'
    if lesson["runnable"]:
        result = subprocess.run(["node", "-e", lesson["code"]], capture_output=True, text=True, check=True)
        lesson["output"] = result.stdout.rstrip()
        body += '<h3>Observed output</h3><pre><code class="language-text">' + html.escape(lesson["output"]) + '</code></pre>'
    body += "<h2>Cost and tradeoffs</h2>" + paragraphs(lesson["cost"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in lesson["mistakes"]) + "</ul>"
    body += "<h2>Continue through the stack</h2><p>" + "; ".join(link(path) for path in lesson["related"]) + ".</p>"
    entry["body"] = body
    entry["data"]["related"] = lesson["related"]
    entry["data"]["reading_minutes"] = max(6, round(len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", body))) / 155))

for project in projects:
    entry = by_path[project["path"]]
    body = paragraphs(project["summary"] + " The deliverable is a working local implementation and a written trace of its boundary decisions. The trace should state what request was made, which layer accepted or rejected it, and what the user saw. This keeps the review tied to behavior instead of the amount of framework code produced.")
    for title, content in project["sections"]:
        body += f"<h2>{html.escape(title)}</h2>" + paragraphs(content)
    body += '<h2>Acceptance contract</h2><pre><code class="language-text">' + html.escape(project["code"]) + '</code></pre>'
    body += '<h3>Common Mistakes</h3><ul>' + ''.join(f'<li>{html.escape(item)}</li>' for item in project["mistakes"]) + '</ul>'
    body += '<h2>Related lessons</h2><p>' + '; '.join(link(path) for path in project["related"]) + '.</p>'
    entry["body"] = body
    entry["data"]["related"] = project["related"]

for path, title, summary in sections:
    group = [lesson for lesson in lessons if lesson["section"] == path]
    entry = by_path[path]
    entry["data"]["modules"] = [{"title": title, "summary": summary, "lessons": [lesson["path"] for lesson in group]}]
    entry["data"]["resource_tabs"] = [{"title": "Web Development", "path": subject_root}, {"title": "Projects", "path": project_hub}, {"title": "Quizzes", "path": quiz_hub}]
    body = f'<p>{html.escape(summary)} The three lessons in this section follow a single inspection workflow, so the request, browser behavior, server decision, and visible result can be checked together.</p>'
    body += '<h2>Lessons</h2><ul>' + ''.join(f'<li>{link(lesson["path"])} — {html.escape(lesson["summary"])}</li>' for lesson in group) + '</ul>'
    body += '<h2>Continue across the track</h2><p>' + '; '.join(link(other) for other, _, _ in sections if other != path) + '; ' + link(project_hub) + '; ' + link(quiz_hub) + '.</p>'
    entry["body"] = body

intro_pages = {
    "web-tech/getting-started": ("Web Development: follow one request through the stack", "Trace a case page from a URL to the displayed response.",
        "A web application is a chain of contracts. A browser resolves a URL, sends a request, receives a response, parses markup, applies styles, and runs only the scripts needed for interaction. The server may read or change data, but it must decide what the caller is allowed to do. If one layer silently assumes another layer has validated input, the application can appear correct in a demo and fail under a direct request. Start with a case record that exists as HTML before enhancement runs. Draw the GET request and identify its path, status, content type, and body. Then add a form for an inspection note and follow its POST through parsing, validation, authorization, storage, and response. Test the same page with scripts disabled and with an unavailable API. A visible failure state is part of the contract, not polish added after the happy path.",
        ["web-tech/http-request-response-contract", "web-tech/browser-parse-load-and-render", "html/html-tutorial", "css/css-tutorial", "javascript/javascript-tutorial"]),
    "web-tech/core-concepts": ("Web Development: assign authority to the right layer", "Separate browser convenience from server authority and stored truth.",
        "The browser owns interaction, presentation, and local navigation. It can help a person fill a form, display progress, and cancel an obsolete read. It does not own record permission or the final stored-data rule. The server validates incoming bytes, checks identity and authorization, chooses a response status, and decides whether a mutation commits. Storage holds durable records under that server contract; browser storage is suitable only for convenience state that can be lost or edited. An origin limits what one page's script can read from another origin, but it does not authorize a caller to edit case 47. A cookie can carry a session reference, yet the server must look it up on every protected request. A cache can save transfer work, yet a private response must not be served to another person. These distinctions make failure cases easier to reason about: ask which layer observed the failure, which layer can repair it, and which layer must reject unsafe input.",
        ["web-tech/url-origin-and-query-boundary", "web-tech/form-server-validation", "web-tech/session-cookie-and-csrf-boundary", "web-tech/cache-etag-revalidation"]),
    "web-tech/practice-project": ("Practice project: trace a case page across the stack", "Map the read, edit, and failure paths of one case record.",
        "Use case 47 as a small system exercise. Sketch a GET page route that returns a semantic case record and a POST inspection route that validates a short note. Give each route a status contract for success, missing data, invalid input, and lack of permission. Keep the initial case title in HTML. Add a form with a label and an error summary, then use one script to enhance its result without destroying native submission. Trace a valid note, an empty note, a missing session, and a network interruption. For each trace, state whether storage changes and what a keyboard user sees. Finally, measure the page once, reserve image dimensions, and run a read-only release check against the deployed route. The goal is a coherent boundary map. The linked projects expand this small trace into a full intake path and a release gate.",
        ["web-tech/case-intake-end-to-end-project", "web-tech/web-release-readiness-project", "web-tech/accessible-feedback-and-keyboard", "web-tech/release-smoke-and-rollback"]),
}

for path, (title, summary, content, related) in intro_pages.items():
    entry = by_path[path]
    entry.update(title=title, summary=summary, updated_at=stamp)
    entry["data"].update(content_format="html", seo_ready=False, reading_minutes=6, related=related)
    entry["body"] = paragraphs(content) + '<h3>Common Mistakes</h3><ul><li>Do not assume a browser check is a server rule.</li><li>Do not judge the full page by its response status alone.</li><li>Do not hide a failed operation without a visible recovery path.</li></ul><h2>Continue</h2><p>' + '; '.join(link(item) for item in related) + '.</p>'

intro_code = {
    "web-tech/getting-started": ("javascript", '''const caseTarget = new URL("/cases/47", window.location.origin);
const response = await fetch(caseTarget);
if (!response.ok) throw new Error(`Case read failed: ${response.status}`);
const caseRecord = await response.json();
document.querySelector("#case-title").textContent = caseRecord.title;''',
        "This one read spends O(B) time and memory decoding a response of B bytes. The page should still include essential case text in its initial HTML; this fetch can refresh details, but cannot be the sole route to understanding the record."),
    "web-tech/core-concepts": ("javascript", '''function acceptInspection({ reviewerId, assignedCases, caseId, note }) {
  if (!assignedCases.get(reviewerId)?.has(caseId)) return { status: 403 };
  if (typeof note !== "string" || !note.trim()) return { status: 422 };
  return { status: 201, note: note.trim() };
}''',
        "For an in-memory set of assignments, the permission check is expected O(1); trimming a note of length L is O(L). A real write adds durable storage and concurrency costs. The browser may offer an early error message, but this server decision must remain authoritative."),
    "web-tech/practice-project": ("javascript", '''const expectedPaths = ["/cases/47", "/api/cases/47"];
async function inspectReadPaths(baseLocation) {
  for (const path of expectedPaths) {
    const response = await fetch(new URL(path, baseLocation));
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
  }
  return expectedPaths.length;
}''',
        "For P paths, this sequential smoke check makes P requests and stores only one response at a time. It proves route availability at one moment, not write behavior, accessibility, performance, or rollback compatibility; those need their own checks.")
}
for path, (language, code, cost) in intro_code.items():
    entry = by_path[path]
    insertion = '<h2>Working contract</h2><pre><code class="language-' + language + '">' + html.escape(code, quote=False) + '</code></pre><h2>Cost and tradeoffs</h2>' + paragraphs(cost)
    entry["body"] = entry["body"].replace('<h3>Common Mistakes</h3>', insertion + '<h3>Common Mistakes</h3>')

root_entry = by_path[subject_root]
root_entry.update(title="Web Development Tutorial", summary="Follow requests, browser interaction, trust boundaries, accessibility, performance, and release checks in one connected track.", updated_at=stamp)
root_entry["data"].update(content_format="html", seo_ready=False,
    resource_tabs=[{"title": "Tutorial", "path": subject_root}, {"title": "Projects", "path": project_hub}, {"title": "Quizzes", "path": quiz_hub}],
    modules=[{"title": "Start here", "summary": "Map the full request path.", "lessons": list(intro_pages)}] +
            [{"title": title, "summary": summary, "lessons": [path] + [lesson["path"] for lesson in lessons if lesson["section"] == path]} for path, title, summary in sections] +
            [{"title": "Apply and check", "summary": "Build and verify the contracts.", "lessons": [project_hub, quiz_hub]}])
root_body = '<p>Web development connects a browser request to a server decision and a result a person can use. Start with the request contract, then follow one inspection workflow through the DOM, validation, state, accessibility, performance, and release. Each lesson names the layer that owns a rule, gives a concrete case, and links to the next boundary.</p>'
root_body += '<h2>Starting points</h2><p>' + '; '.join(link(path) for path in intro_pages) + '.</p>'
for path, title, summary in sections:
    root_body += f'<h2>{link(path, title)}</h2><p>{html.escape(summary)}</p><ul>' + ''.join(f'<li>{link(lesson["path"])} — {html.escape(lesson["summary"])}</li>' for lesson in lessons if lesson["section"] == path) + '</ul>'
root_body += '<h2>Build and test</h2><p>' + link(project_hub) + '; ' + link(quiz_hub) + '.</p>'
root_body += '<h2>Go deeper by language</h2><p>' + '; '.join(link(path) for path in ["html/html-tutorial", "css/css-tutorial", "javascript/javascript-tutorial"]) + '.</p>'
root_entry["body"] = root_body

project_hub_entry = by_path[project_hub]
project_hub_entry.update(title="Web Development Projects", summary="Apply browser, server, and release contracts in two end-to-end builds.", category="Web Development", subject="web-tech", tags=["web-tech", "web-development"], updated_at=stamp)
project_hub_entry["data"].update(content_format="html", seo_ready=False,
    modules=[{"title": "Projects", "summary": "Build, trace, and verify.", "lessons": ["web-tech/practice-project"] + [project["path"] for project in projects]}],
    resource_tabs=[{"title": "Tutorial", "path": subject_root}, {"title": "Quizzes", "path": quiz_hub}])
project_hub_entry["body"] = '<p>Build one inspection workflow at a time. State the request and storage contract first, then prove the accessible browser path and deployed route. Each project includes failure cases to test, so a passing demo cannot hide a broken write or release gate.</p><h2>Projects</h2><ul>' + ''.join('<li>' + link(path) + '</li>' for path in ["web-tech/practice-project"] + [project["path"] for project in projects]) + '</ul><h2>Related track</h2><p>' + link(subject_root) + '; ' + link(quiz_hub) + '.</p>'

quiz_hub_entry = by_path[quiz_hub]
quiz_hub_entry["data"].update(modules=[{"title": "Quizzes", "summary": "Check the decision boundaries.", "lessons": [path for path, _, _ in quiz_specs]}],
    resource_tabs=[{"title": "Tutorial", "path": subject_root}, {"title": "Projects", "path": project_hub}])
quiz_hub_entry["body"] = '<p>Use these questions after tracing the case workflow. The first set checks request and browser behavior; the second checks state, trust, accessibility, and release. Every answer includes the reason, so a mistake can point back to a specific lesson.</p><h2>Quizzes</h2><ul>' + ''.join('<li>' + link(path) + '</li>' for path, _, _ in quiz_specs) + '</ul><h2>Continue</h2><p>' + link(subject_root) + '; ' + link(project_hub) + '.</p>'
for path, title, _ in quiz_specs:
    quiz_entry = by_path[path]
    quiz_entry["body"] = '<p>' + html.escape(title) + ' checks decisions from the case workflow. Choose an answer, read the explanation, and reopen the linked lesson when the boundary is unclear. The questions focus on observable request and page behavior rather than memorized syntax.</p><h2>Related lessons</h2><p>' + link(subject_root) + '; ' + link("web-tech/http-request-response-contract") + '; ' + link("web-tech/session-cookie-and-csrf-boundary") + '; ' + link("web-tech/release-smoke-and-rollback") + '.</p>'

reciprocal = {
    "html/forms-get-post": "web-tech/form-server-validation",
    "html/form-validation": "web-tech/form-server-validation",
    "html/form-help-and-errors": "web-tech/accessible-feedback-and-keyboard",
    "html/anchors-and-paths": "web-tech/url-origin-and-query-boundary",
    "html/document-skeleton": "web-tech/browser-parse-load-and-render",
    "html/script-loading": "web-tech/browser-parse-load-and-render",
    "html/responsive-images": "web-tech/performance-budget-and-layout-stability",
    "html/form-labels": "web-tech/accessible-feedback-and-keyboard",
    "html/live-status": "web-tech/dom-events-progressive-enhancement",
    "css/responsive-layout": "web-tech/performance-budget-and-layout-stability",
    "javascript/javascript-tutorial": "web-tech/fetch-status-and-abort",
}
for path, target in reciprocal.items():
    entry = by_path[path]
    addition = '<p>Continue with the connected Web Development lesson: ' + link(target) + '.</p>'
    if addition not in entry["body"]:
        entry["body"] += '\n' + addition
        entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"entries": len(entries), "web_development_routes": len([e for e in entries if e["path"].startswith("web-tech/")]),
                  "lessons": len(lessons), "projects": len(projects), "quizzes": len(quiz_specs),
                  "runnable_examples": sum(bool(lesson["runnable"]) for lesson in lessons)}))

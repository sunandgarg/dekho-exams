"""Add original rendering/data-flow and form-workflow lessons to AI Trove drafts."""

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
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def paragraph(value):
    return f"<p>{html.escape(value)}</p>"


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


hubs = [
    dict(path="web-tech/server-rendering-and-client-data-flow", title="Server Rendering and Client Data Flow",
         summary="Keep the first render deterministic, then give client-held records clear freshness and mutation rules.",
         overview="A server can send useful HTML before the browser runs application code, but the first client render must agree with that HTML. Once the page is interactive, its data has a second problem: a visible record may be older than the server copy, or a quick edit may fail after the interface has already shown success. This track assigns ownership to each step: server snapshot, hydration, client cache, and mutation. The running case is a review queue where staff can open the same case from several routes and devices.",
         bridges=["web-tech/server-rendered-static-and-client-rendered-pages", "web-tech/react-effects-and-request-races", "web-tech/conditional-writes-and-lost-update-prevention"]),
    dict(path="web-tech/forms-and-data-entry-workflows", title="Forms and Data Entry Workflows",
         summary="Make submission, validation, autosave, and large uploads recoverable under real browser conditions.",
         overview="A form is a transaction with a human in the loop. The browser can provide labels, native validation, keyboard submission, and a real request even if application JavaScript fails to load. Enhancements such as asynchronous checks, autosave, and file progress add more states, not fewer. These lessons follow a case-intake form from the submitter button through server validation, delayed field checks, local draft recovery, and upload completion. Each step distinguishes an on-device preview from a server-accepted record.",
         bridges=["web-tech/form-server-validation", "web-tech/form-errors-and-recovery-paths", "web-tech/safe-file-upload-pipeline"]),
]

topics = [
    dict(hub=0, path="web-tech/hydration-and-deterministic-first-render", title="Hydration and Deterministic First Render",
         summary="Make server HTML and the browser's initial component tree agree before reading browser-only state.",
         definition="Hydration attaches client behavior to HTML that the server has already produced. Its first comparison is a correctness boundary: the initial client tree must describe the same content and structure as the server output. A date formatted in different time zones, a random identifier, or a browser-only preference read during render can break that agreement. Decide which values are part of the request snapshot, serialize them safely, and render them unchanged for the first client pass. Browser-only preferences can update after hydration, with a reserved space or stable placeholder where a change would otherwise shift the page.",
         case="The review queue server renders case 47 as 'Pending' and a timestamp in its configured time zone. A reviewer opens the page in another time zone; the browser reformats the timestamp before hydration completes. The client now expects a different text node. Keep the first timestamp as a stable machine value and display format agreed by both sides, then change to the reviewer's locale after mount if the product requires it. The case status is more serious: it must come from the same server snapshot, not a stale browser cache read during the initial render.",
         code='function firstRenderCase(snapshot) {\n  return { caseId: snapshot.caseId, status: snapshot.status, updatedAt: snapshot.updatedAt };\n}\nconst serverSnapshot = { caseId: 47, status: "Pending", updatedAt: "2026-10-04T08:12:00Z" };\nconsole.log(JSON.stringify(firstRenderCase(serverSnapshot)) === JSON.stringify(firstRenderCase(serverSnapshot)));\n// Output: true',
         implementation="The small function makes the intended invariant visible: both environments receive the same serialized snapshot. In a real component, avoid reading localStorage, window size, or a current clock value during the first render. A post-hydration effect may read those values and update presentation. Keep user-specific HTML behind the right authentication and cache policy; deterministic output is not permission to serve one person's snapshot to another. Test rendered HTML and hydrated DOM with the same input, then repeat under another locale and time zone.",
         cost="Server rendering adds work and bytes on the server, while hydration still loads client JavaScript for interactive regions. For n rendered case rows, creating the first tree is O(n) in the number of rows and carries corresponding DOM memory; reformatting every row after mount adds another O(n) pass. A small, stable first view may feel faster than an empty shell, but duplicate work and large serialized snapshots can erase the benefit. Measure first content, interaction readiness, and mismatch logs together rather than relying on a single loading metric.",
         failure="A developer replaces the initial status with a value from localStorage to make navigation appear instant. On a cold entry the server shows Pending, while the client reads Resolved from a previous session. Hydration reports a mismatch, and the visible label may flicker. Another developer suppresses the warning without resolving the conflicting source of truth. Preserve the server snapshot for the first pass, then fetch or reconcile current data explicitly; a warning suppression should be limited to a genuinely unavoidable text difference, not used to hide a broken data contract.",
         drill="Render case 47 in two time zones and with two stored preference values. Capture server HTML before scripts and the first client tree, then compare status, timestamp, and element order. Simulate a stale stored status and verify the first render still follows the request snapshot. After hydration, apply the local preference and observe whether layout shifts. Finally test a second account on a shared cache path; its HTML must never contain case 47 unless that account is allowed to see it.",
         decision="Treat the server response as the exact first-render snapshot and move browser-only reads to a later, owned update.",
         checks=["Server HTML and first client tree agree across time zones.", "A stale local preference cannot alter the initial record status.", "A second account never receives another reviewer's serialized case."],
         mistakes=["Calling a clock or random generator in initial render.", "Reading browser storage before hydration for visible server content.", "Silencing a mismatch while its data sources still disagree."],
         related=["web-tech/server-rendered-static-and-client-rendered-pages", "web-tech/react-effects-and-request-races", "web-tech/output-escaping-and-csp"]),
    dict(hub=0, path="web-tech/server-data-bootstrap-and-freshness", title="Server Data Bootstrap and Freshness",
         summary="Pass request data to the client without cross-request leaks or a pointless immediate refetch.",
         definition="A page often loads a record on the server so the initial HTML has useful content. The browser then needs enough of that same record to continue without asking for it again before the user can act. Transfer a minimal, safely encoded snapshot with a stable record key and a version or update time. The client should know when that snapshot was obtained and when it becomes stale. A request-scoped cache is essential on the server: a process-global cache keyed too loosely can hand one reviewer's private case to another request. The bootstrap is a starting value, not a permanent claim of freshness.",
         case="Reviewer 29 opens case 47 through a direct link. The server already fetched its title, state, and version 6 to render the page. If the client starts with an empty cache, it flashes a loading state and immediately fetches the same record again. Bootstrap the client with the server's exact response and retrieval time, then choose a short stale interval for case status. A later return to the route may trigger a background refresh, but the old snapshot should be labeled or retained according to the product's tolerance for stale data.",
         code='function shouldRefresh(snapshot, nowMilliseconds, maxAgeMilliseconds) {\n  if (!snapshot || !Number.isFinite(snapshot.fetchedAt)) return true;\n  return nowMilliseconds - snapshot.fetchedAt >= maxAgeMilliseconds;\n}\nconsole.log(shouldRefresh({ fetchedAt: 1000 }, 2200, 1500));\n// Output: false',
         implementation="The freshness calculation is deliberately separate from rendering. In production, use a monotonic duration where possible for in-session timing and an explicit server timestamp for a serialized cross-environment record. Validate the bootstrap shape at the boundary; never insert raw serialized data into a script context without safe escaping. Include user and authorization scope in server cache ownership, and discard client records after sign-out. The page should define whether stale case details stay visible during refresh, whether edits are disabled, and what happens when the refresh returns an access denial.",
         cost="Bootstrapping avoids an avoidable request but increases HTML payload by the size of the snapshot. A minimal record of k fields costs O(k) serialization and client storage; duplicating a long activity history can dominate the document and delay parsing. A longer freshness window reduces network traffic but increases the chance of showing an obsolete status. A short window does the opposite. Choose the window by the consequence of stale data, not by one global default, and measure duplicate requests on cold entry and route return.",
         failure="A shared server query cache stores case 47 under the key 'case' and survives the request. A second reviewer receives a response that contains the first reviewer's private details. Even if the UI refetches later, the leak already happened in HTML. Build the cache per request or isolate it by authorization context, and use a complete record key. Another failure is marking the bootstrap fresh forever; a resolved case remains Pending in a tab reopened hours later. Preserve the fetched time and revalidation rule across route transitions.",
         drill="Load case 47 directly and count network reads before the first edit. The record should arrive in HTML and not trigger a redundant request within the chosen freshness window. Open case 62 under a second account, then inspect the HTML and client cache for any trace of 47. Advance the clock beyond the window and return to 47; verify revalidation occurs and that the UI gives a clear state while the request runs. Sign out and confirm the client-held private snapshot is removed.",
         decision="Bootstrap only the data needed for first interaction, with request scope and an explicit refresh deadline.",
         checks=["Cold entry avoids a duplicate immediate record request.", "Separate accounts cannot observe each other's bootstrapped data.", "A stale snapshot revalidates under a documented UI state."],
         mistakes=["Using a process-wide private query cache across requests.", "Serializing an entire history when the first view needs only a summary.", "Treating bootstrap data as fresh without a timestamp or version."],
         related=["web-tech/cache-etag-revalidation", "web-tech/record-level-authorization", "web-tech/server-rendered-static-and-client-rendered-pages"]),
    dict(hub=0, path="web-tech/client-cache-keys-and-invalidation", title="Client Cache Keys and Invalidation",
         summary="Give each cached view a complete identity and refresh the views affected by a write.",
         definition="A client cache maps a request identity to a result. Its key must include every input that changes the response: record ID, filter, page, locale when content differs, and account or tenant boundary where relevant. An incomplete key makes two distinct screens share data. After a write, invalidate or update the exact affected records and lists. A record detail and a filtered queue can both describe the same case, so refreshing one does not necessarily repair the other. Start with a small key vocabulary that matches server request contracts, and keep private caches isolated at sign-out or account switch.",
         case="A reviewer resolves case 47 while viewing the Pending queue. The detail panel changes to Resolved, but the Pending list still contains 47 because only the detail key was updated. If the list key omits filter and account, another route may even reuse the wrong queue. Define separate keys for the case record and each queue filter. On successful resolution, update or invalidate the case detail, the Pending list, and the Resolved list. A version in the server response can prevent an older background fetch from overwriting a newer mutation result.",
         code='function caseKey(accountId, caseId) { return ["case", accountId, caseId]; }\nfunction queueKey(accountId, state, page) { return ["queue", accountId, state, page]; }\nconsole.log(JSON.stringify(caseKey(29, 47)));\n// Output: ["case",29,47]',
         implementation="Use stable primitive key parts; avoid putting a freshly created object in a key unless the cache library normalizes it predictably. Keep a dependency map from a mutation to affected views: detail, membership lists, counters, and any search result that displays status. Invalidate when computing the replacement is hard or partial; write through when the server response contains the authoritative next record. In either case, guard against a fetch started before the mutation completing afterward. A query cache is a view optimization, never the authority for write authorization.",
         cost="A key lookup is usually near O(1) in a map-backed cache, but invalidating m related views can trigger up to m network reads and renders. Broad invalidation is simpler and potentially costly; narrow updates are faster but can miss a view. Cache memory grows with distinct account, filter, page, and record combinations, so expiration and sign-out clearing matter. Measure stale membership bugs and duplicate fetches together. The right policy is the smallest reliable set of affected views, not the smallest possible line count.",
         failure="The key ['queue', 'Pending'] omits account ID. Reviewer 29 switches to an account that should not see case 47; the old list remains visible until a refetch finishes. A second defect appears when a background Pending request started before resolution returns after the mutation and puts 47 back in the list. Include account scope in keys, clear private data on account switch, cancel or version stale requests, and invalidate every list whose membership can change. Test with delayed responses, not only fast local networking.",
         drill="Create Pending and Resolved queues for accounts 29 and 62, then resolve case 47. Record which keys change and which fetches run. Delay a pre-mutation Pending response until after the write succeeds; 47 must not reappear. Switch accounts without a page reload and check for any old private row. Add page and filter variants, then verify a key change actually produces a different cache entry. Document how the cache expires when the tab stays open for an hour.",
         decision="Key by the whole response identity and invalidate the complete set of views whose content or membership the write changes.",
         checks=["A resolved case leaves Pending and appears in Resolved after the write.", "Delayed old reads cannot replace a newer result.", "Account switches expose no rows from the prior account."],
         mistakes=["Leaving filter or account scope out of a key.", "Refreshing a detail record but forgetting list membership.", "Assuming an old request cannot finish after a newer write."],
         related=["web-tech/cache-etag-revalidation", "web-tech/conditional-writes-and-lost-update-prevention", "web-tech/record-level-authorization"]),
    dict(hub=0, path="web-tech/optimistic-mutations-and-rollback", title="Optimistic Mutations and Rollback",
         summary="Show immediate feedback without turning a failed write into a false success.",
         definition="An optimistic update changes the local view before the server confirms a write. It is useful when the expected result is common and delay would interrupt a task, but the UI now owns a temporary state that may need correction. Capture the previous cache value, identify the mutation, and mark the pending state visibly. If the server accepts the write, replace local data with its authoritative response and version. If it rejects the write, restore or reconcile the affected views and tell the user what happened. A rollback snapshot alone is insufficient when two writes overlap or another actor changes the same record.",
         case="Reviewer 29 changes case 47 from Pending to Resolved. The queue removes it immediately, while a small pending label remains until the server confirms version 7. If the request fails because version 6 is stale, restoring the old row blindly may still be wrong: another reviewer may already have reassigned the case. Fetch the authoritative record, show the conflict, and let the reviewer decide whether to retry with the new version. A transport timeout is different from a known rejection; the server may have committed the write, so use an idempotency key or query status before retrying.",
         code='function optimisticState(previousRecord, nextStatus) {\n  return { previous: previousRecord, pending: { ...previousRecord, status: nextStatus } };\n}\nconst change = optimisticState({ caseId: 47, status: "Pending", version: 6 }, "Resolved");\nconsole.log(change.pending.status, change.previous.version);\n// Output: Resolved 6',
         implementation="The example captures an immutable before-image and a visible pending value. In a real cache, snapshot every affected key or choose targeted invalidation after completion, since list membership and counters also change. Tie callbacks to a mutation ID so an older failure cannot roll back a newer successful edit. Send the record version as a conditional write and a stable idempotency key for retryable operations. Distinguish retryable network uncertainty, validation rejection, permission denial, and version conflict in UI copy; each demands a different recovery action.",
         cost="The local transformation costs O(k) for k copied record fields and at least one additional record in memory until the write settles. Updating multiple cached lists can cost O(n) in their combined row counts; invalidation trades local work for network reads. Immediate perceived response is valuable, but complexity rises with concurrent edits and uncertain outcomes. For a destructive or legally meaningful action, waiting for server confirmation may be the better product choice. Measure error rate and repair burden before making every write optimistic.",
         failure="Two status changes start in order: Resolve, then Reopen. The second succeeds first; the first later fails. A naïve rollback restores Pending and overwrites the successful Reopen result. Give each mutation an identity and reconcile by server version rather than applying every old snapshot unconditionally. Another failure is calling a timeout a rejection and encouraging a duplicate retry when the first request actually committed. Use a stable retry key and inspect the authoritative state before showing a second success.",
         drill="Delay two writes and settle their responses in reverse order. Confirm that a late failure cannot erase the newer accepted state. Force a version conflict and verify the interface presents the server record rather than silently restoring stale data. Simulate a request timeout after the server commits, then retry with the same idempotency key and count actual writes. Finally test a permission denial; the optimistic state must disappear and the user must see a specific error, not a generic success toast.",
         decision="Use optimistic UI only when the temporary state has an explicit owner, confirmation path, and conflict repair path.",
         checks=["A failed write does not leave a false success on screen.", "Reverse-order responses preserve the newest accepted version.", "A timeout retry cannot apply the same mutation twice."],
         mistakes=["Rolling back without checking later mutations.", "Treating timeout as proof that the server rejected the write.", "Updating one cache view while leaving related lists inconsistent."],
         related=["web-tech/idempotent-write-requests", "web-tech/conditional-writes-and-lost-update-prevention", "web-tech/form-errors-and-recovery-paths"]),
    dict(hub=1, path="web-tech/native-form-submission-and-progressive-enhancement", title="Native Form Submission and Progressive Enhancement",
         summary="Keep a working server submission path, then add client behavior without bypassing browser form rules.",
         definition="A real HTML form provides keyboard submission, labels, successful-control serialization, and browser constraint validation without application JavaScript. Give it a server action and method that can complete the core task. JavaScript may intercept submission for quicker feedback, but it should preserve the form's contract and allow a fallback when scripts fail. The clicked submitter can carry a name and value, which matters when Save draft and Submit are different actions. The submit() method bypasses validation and the submit event; requestSubmit() follows normal submission behavior and can name the intended submitter.",
         case="The case-intake screen has Save draft and Send for review buttons. A developer adds an autosave handler that calls form.submit() after a field blur, unintentionally skipping required-field checks and omitting which button was chosen. The server receives an ambiguous request. Keep separate submitter values and use requestSubmit() when code must initiate a normal submission. The server validates both actions and returns field errors with the user's values. If the bundle fails to load, a direct form POST still reaches a useful response rather than leaving a dead button.",
         code='function submitForReview(formElement, reviewButton) {\n  if (!formElement.reportValidity()) return false;\n  formElement.requestSubmit(reviewButton);\n  return true;\n}',
         implementation="Use semantic labels, names, types, and a server endpoint; client checks are feedback, not the authority for business rules. In the enhanced path, read the submit event's submitter to distinguish draft from review and use FormData for successful controls. Preserve focus and an error summary when the server rejects a field. Avoid disabling every control during a slow request if the user needs to copy or correct data; disable the specific duplicate action or use a pending state. Prevent default only after the enhancement is ready to take responsibility for response and error handling.",
         cost="Native submission has browser-managed navigation and request behavior, which may be sufficient for an administrative flow. Interception adds code for pending, abort, retries, history, and focus repair. Serializing f fields is O(f), and the form payload grows with the entered values and files. A client validation pass can avoid an obvious round trip but cannot replace server validation. Choose enhancement only where it improves a measured workflow and still test the no-script and failed-script paths.",
         failure="An engineer renders a clickable div instead of a submit button. Mouse testing passes, but Enter in a field does nothing and keyboard focus is unclear. Another engineer calls form.submit() to 'fix' it, bypassing browser validation and the intended submitter. Use a real button with a type and name, preserve native form semantics, and call requestSubmit(button) only when programmatic initiation is necessary. Test with JavaScript disabled and with the bundle timing out, then confirm the server response keeps entered values and explains the next step.",
         drill="Create a case-intake form with Save draft and Send for review. Disable JavaScript and complete both paths using only keyboard input. Turn enhancement back on and compare the serialized submitter for each button. Leave a required field blank and invoke each programmatic method in a controlled test; record which one runs validation. Force the server to reject a valid-looking client value and confirm the field error remains visible, focused, and associated with the input.",
         decision="Build a real form and server response first; let scripts enhance submission only when they preserve validation and recovery.",
         checks=["Both submitter actions work without JavaScript.", "Programmatic review submission respects native constraints.", "Server rejection preserves values and an accessible error path."],
         mistakes=["Using submit() when normal validation and submitter behavior are needed.", "Replacing a submit button with a generic click target.", "Assuming client checks are sufficient server validation."],
         related=["web-tech/dom-events-progressive-enhancement", "web-tech/form-server-validation", "web-tech/accessible-names-and-native-controls"]),
    dict(hub=1, path="web-tech/asynchronous-field-validation-races", title="Asynchronous Field Validation Races",
         summary="Ignore obsolete field responses and keep server validation authoritative at final submission.",
         definition="Asynchronous field checks can tell a user whether a case reference is already used or whether an entered address is eligible. They are advisory while the person is typing. Requests can finish out of order, and an available value can become unavailable before the form is submitted. Give each field edit a generation or value identity, cancel old requests when practical, and apply a response only if it still matches the current input. Do not make the final submit depend solely on an earlier green indicator; the server must validate again while applying the write.",
         case="An operator enters reference 'CASE-47', then corrects it to 'CASE-62'. The CASE-62 check returns available first. A slow CASE-47 response arrives later and replaces the message with 'already used', even though the input now says CASE-62. Capture the value and a request sequence at dispatch. On response, compare both to current state before updating feedback. At submission, the server checks uniqueness and returns a field error if another operator claimed CASE-62 in the meantime. The UI must move focus to the right field without losing the typed value.",
         code='function isCurrentValidation(request, currentValue, currentSequence) {\n  return request.value === currentValue && request.sequence === currentSequence;\n}\nconsole.log(isCurrentValidation({ value: "CASE-47", sequence: 4 }, "CASE-62", 5));\n// Output: false',
         implementation="The identity check remains necessary even when AbortController cancels old fetches, because cancellation may race with a completed response or a non-abortable data source. Debounce only if it reduces wasted requests; show a checking state so silence is not mistaken for approval. Normalize values consistently between client and server, but let the server decide uniqueness in a transaction or database constraint. Associate feedback with the field, announce changes without repeating them on every keystroke, and distinguish network failure from invalid input.",
         cost="For e edits, an eager validator can send O(e) requests; debounce reduces typical traffic but adds feedback delay. Generation tracking takes O(1) state per field, while holding every old promise or controller can accumulate if cleanup is neglected. A uniqueness lookup cost depends on the server index, yet the client cannot infer its final truth from a past lookup. Prefer a modest delay and one active request for expensive checks, then measure request count and the time before actionable feedback on realistic typing speeds.",
         failure="The first response overwrites the second because completion order differs from entry order. The page announces a false error and disables Send for review, trapping the operator. Guard response application by current value and sequence; allow a retry after a network failure. A separate race occurs after the form is submitted: the field looked free, but another operator saved it first. The server returns a conflict tied to the field, and the form must explain it without erasing unrelated entries or presenting the earlier green state as proof.",
         drill="Enter three references quickly, delay the first response until last, and inspect the field message after every completion. Abort one request just as it finishes and verify the generation check still protects the current value. Simulate a temporary network loss and ensure the message reads 'could not check' rather than 'invalid'. Submit a value that was available at check time but taken before write time; the server rejection must attach to the field and preserve the rest of the form.",
         decision="Treat async field feedback as a versioned hint and final server validation as the write boundary.",
         checks=["Out-of-order responses never describe an old field value.", "Network failure is distinct from validation rejection.", "The server can reject a value that was previously shown as available."],
         mistakes=["Assuming abort alone prevents every stale callback.", "Disabling final submit forever after a validation network error.", "Treating an availability check as a reservation."],
         related=["web-tech/react-effects-and-request-races", "web-tech/form-server-validation", "web-tech/accessible-feedback-and-keyboard"]),
    dict(hub=1, path="web-tech/autosave-draft-recovery-and-conflicts", title="Autosave, Draft Recovery, and Conflicts",
         summary="Persist edits without disguising local storage as a confirmed server save.",
         definition="Autosave creates at least three states: changes in the input, a local recoverable copy, and a server-accepted version. Label them separately. A draft can be retained in browser storage for recovery after a tab crash, but that does not mean another device can see it or that the server accepted it. Save after a short idle period or explicit field boundary, send a version with the write, and clear or update the local draft only after confirmation. On reopen, compare local edit time and server version before offering recovery; never silently overwrite a newer server record.",
         case="A reviewer changes the diagnosis of case 47, then loses connection before autosave returns. The browser stores a local draft; the header says 'Saved on this device', not 'Saved to server'. Meanwhile a colleague edits the same case from another browser and advances it to version 8. On reconnect, the first reviewer sees a conflict and chooses which text to keep. The interface preserves both values until a decision is made. A second tab with an older draft must not replace the newer confirmed version merely because its local timestamp is later.",
         code='function draftStatus(localDraft, serverVersion) {\n  if (!localDraft) return "server-only";\n  return localDraft.baseVersion === serverVersion ? "recoverable" : "needs-review";\n}\nconsole.log(draftStatus({ baseVersion: 7, text: "Inspect valve" }, 8));\n// Output: needs-review',
         implementation="Store only the fields necessary for recovery, scoped by account and case ID. Keep sensitive values out of local persistence when policy requires it, and clear drafts on sign-out or record deletion. Attach a base version to each draft; a timestamp alone cannot prove which record state it descends from. Use a conditional server write and an idempotency key for retries. If offline work is supported, queue writes with order and a visible pending count, then reconcile rather than replaying blindly. The status language must reflect the last confirmed boundary.",
         cost="Writing a draft of k bytes is O(k) serialization and storage, repeated after edits; a short debounce reduces write frequency at the cost of a small unsaved window. Browser storage is finite, shared with other origin data, and may be cleared, so it is recovery help rather than a durability guarantee. Each version conflict needs human or domain-specific merge logic. The extra state and UI are justified for long forms, but a tiny low-risk form may need only explicit Save and a leave warning.",
         failure="An autosave request times out, but the UI immediately changes its label to 'All changes saved'. The reviewer closes the tab and later finds the server's old text. Another failure is restoring a local draft solely by its local timestamp, overwriting a colleague's newer version. Keep pending and confirmed states distinct, retain the local copy until a confirmed response, and compare the draft's base version with the server version on reopen. If the server outcome is uncertain, query its current state before retrying.",
         drill="Edit a 120-character diagnosis, interrupt the network after the request leaves, and close the tab. Reopen and identify exactly what is local and what the server accepted. Make a second browser update the record to version 8 before reconnect. Verify the recovery UI displays both versions and requires a choice. Sign out and confirm the draft cannot appear under account 62. Fill browser storage near quota and ensure a failed local write does not create a false 'saved' label.",
         decision="Name each persistence boundary in the UI and use server version checks before replaying a recovered draft.",
         checks=["A local-only draft is never described as a server save.", "Recovery detects a changed server version before applying edits.", "Account switch clears or isolates private local drafts."],
         mistakes=["Using a timestamp as a substitute for the server base version.", "Clearing a local draft before the server confirms the write.", "Ignoring quota and sign-out behavior for browser storage."],
         related=["web-tech/indexeddb-draft-queue", "web-tech/conditional-writes-and-lost-update-prevention", "web-tech/form-errors-and-recovery-paths"]),
    dict(hub=1, path="web-tech/multipart-upload-progress-and-retry-boundaries", title="Multipart Upload Progress and Retry Boundaries",
         summary="Separate file selection, transfer, and server acceptance; retry from a defined upload protocol.",
         definition="Selecting a file does not upload it, completing a network transfer does not prove the server accepted it, and showing a preview does not prove it is safe to serve later. A browser form can send a file with multipart/form-data. When constructing FormData for fetch, let the browser set the Content-Type header so it includes the correct boundary; a hand-written multipart header without that boundary breaks parsing. Progress reporting requires an API or upload protocol that exposes transferred bytes. A large-file resume feature needs an explicit upload ID, chunk positions, integrity checks, expiry, and finalization step on the server.",
         case="The intake form accepts a 47 MB inspection video. A developer shows 'Uploaded' as soon as the browser has sent all bytes, but the server later rejects the file after validation. Change the states to Selected, Transferring, Processing, Accepted, or Rejected. For a small file, one multipart request may be enough. For larger files on unstable connections, split into bounded chunks only if the server supports session ownership and idempotent chunk retries. A cancelled upload must release on-device preview URLs and tell the server to expire or discard unfinished data.",
         code='async function sendEvidence(formElement, endpoint) {\n  const payload = new FormData(formElement);\n  const response = await fetch(endpoint, { method: "POST", body: payload });\n  if (!response.ok) throw new Error("Evidence was not accepted");\n  return response.json();\n}',
         implementation="The browser adds the multipart boundary when given FormData; do not set that Content-Type manually. The server still checks authorization, size, media type from inspected bytes, storage quotas, and malware policy before attaching a file to a case. Fetch does not provide a simple cross-browser upload progress event through this pattern, so a product requiring byte progress needs a supported transport or a separate chunk protocol. Retrying a complete one-shot POST can duplicate the file unless the server uses a stable request identity. Keep the upload's temporary ID scoped to the account and case.",
         cost="A single multipart transfer costs O(b) bytes for a file of size b, plus protocol overhead; building large blobs in JavaScript can add O(b) memory on top of the browser's file handle. Chunking with c-byte parts adds roughly O(b/c) requests and metadata operations, but permits bounded retry of a failed part. Each server-side temporary object consumes storage until accepted or expired. Select thresholds from measured network conditions and server limits, and do not add a resume protocol to a form that only accepts tiny attachments.",
         failure="The client sets Content-Type: multipart/form-data by hand, omitting the boundary; the server reports an empty file even though the browser sent bytes. Remove that header and let FormData control it. A second failure occurs when the server returns 202 for processing and the UI calls the upload Accepted immediately. Wait for final validation or show Processing with a status check. If a chunk retry arrives twice, the server must recognize the same upload ID and byte range rather than appending duplicate bytes.",
         drill="Submit a small file using a native form and FormData, then inspect the request boundary in developer tools. Break the manually set header in a controlled branch and confirm the server refuses it. For a simulated large file, interrupt the third chunk, retry the same range, and verify the final byte length and checksum. Reject the file after transfer and check that the interface says Rejected rather than Uploaded. Cancel midway and verify preview URL cleanup and temporary server-data expiry.",
         decision="Represent upload states honestly and introduce resumable chunks only with server-owned identity, integrity, and finalization.",
         checks=["Multipart requests include a browser-generated boundary.", "Transfer completion does not imply server acceptance.", "A repeated chunk cannot duplicate bytes or attach a file twice."],
         mistakes=["Manually setting multipart Content-Type for FormData fetch.", "Treating a local preview as a validated server asset.", "Retrying a non-idempotent upload without a stable upload identity."],
         related=["web-tech/safe-file-upload-pipeline", "web-tech/idempotent-write-requests", "web-tech/browser-memory-and-resource-lifecycles"]),
]

assert len(hubs) == 2 and len(topics) == 8
assert [sum(topic["hub"] == hub for topic in topics) for hub in (0, 1)] == [4, 4]


def add_entry(path, title, summary, entry_type, section_path, order):
    assert path not in by_path, path
    template = "web-tech/getting-started" if entry_type == "article" else "web-tech/web-technology"
    entry = copy.deepcopy(by_path[template])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), type=entry_type,
                 path=path, title=title, summary=summary, category="Web Development",
                 subject="web-tech", difficulty="Intermediate" if entry_type == "article" else None,
                 tags=["web-tech", "web-development"], sort_order=2100 + order,
                 status="published", created_at=stamp, updated_at=stamp, published_at=stamp, body="")
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": section_path,
                     "content_format": "html", "seo_ready": False}
    if entry_type == "article":
        entry["data"].update(kind="tutorial", author_path="authors/aitrove-editorial", reading_minutes=8)
    entries.append(entry)
    by_path[path] = entry
    return entry


for number, hub in enumerate(hubs):
    add_entry(hub["path"], hub["title"], hub["summary"], "subject", hub["path"], number)
for number, topic in enumerate(topics):
    add_entry(topic["path"], topic["title"], topic["summary"], "article", hubs[topic["hub"]]["path"], 10 + number)

for topic in topics:
    entry = by_path[topic["path"]]
    subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"],
                   text=True, capture_output=True, check=True)
    siblings = [item["path"] for item in topics if item["hub"] == topic["hub"] and item["path"] != topic["path"]]
    related = [hubs[topic["hub"]]["path"]] + siblings + topic["related"]
    body = paragraph(topic["definition"])
    body += "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>"
    body += paragraph(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + paragraph(topic["cost"])
    body += "<h2>Failure trace</h2>" + paragraph(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join(f"<li>{html.escape(check)}</li>" for check in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + paragraph(topic["drill"])
    body += "<h2>Decision note</h2>" + paragraph(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in topic["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><p>" + "; ".join(link(path) for path in related) + ".</p>"
    entry["body"] = body
    entry["data"].update(related=related, reading_minutes=max(6, round(len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", body))) / 155)))

for hub in hubs:
    entry = by_path[hub["path"]]
    group = [topic for topic in topics if hubs[topic["hub"]]["path"] == hub["path"]]
    entry["data"]["modules"] = [{"title": hub["title"], "summary": hub["summary"], "lessons": [topic["path"] for topic in group]}]
    entry["data"]["resource_tabs"] = [{"title": "Web Development", "path": "web-tech/web-technology"},
                                     {"title": "Projects", "path": "web-tech/web-technology/project"},
                                     {"title": "Quizzes", "path": "web-tech/quizzes"}]
    entry["body"] = paragraph(hub["overview"])
    entry["body"] += "<h2>Topics in this track</h2><ul>" + "".join(f'<li>{link(topic["path"])} — {html.escape(topic["summary"])}</li>' for topic in group) + "</ul>"
    entry["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in hub["bridges"]) + ".</p>"
    entry["body"] += "<h2>Neighbor track</h2><p>" + link(hubs[0]["path"] if hub == hubs[1] else hubs[1]["path"]) + ".</p>"

root_entry = by_path["web-tech/web-technology"]
for hub in hubs:
    group = [topic for topic in topics if hubs[topic["hub"]]["path"] == hub["path"]]
    root_entry["data"]["modules"].append({"title": hub["title"], "summary": hub["summary"],
                                          "lessons": [hub["path"]] + [topic["path"] for topic in group]})
    root_entry["body"] += f'<h2>{link(hub["path"])}</h2><p>{html.escape(hub["summary"])}</p><ul>' + "".join(
        f'<li>{link(topic["path"])} — {html.escape(topic["summary"])}</li>' for topic in group) + "</ul>"
root_entry["updated_at"] = stamp

crosslinks = {
    "web-tech/server-rendered-static-and-client-rendered-pages": [hubs[0]["path"], topics[0]["path"]],
    "web-tech/react-effects-and-request-races": [topics[0]["path"], topics[5]["path"]],
    "web-tech/cache-etag-revalidation": [topics[1]["path"], topics[2]["path"]],
    "web-tech/conditional-writes-and-lost-update-prevention": [topics[3]["path"], topics[6]["path"]],
    "web-tech/form-server-validation": [hubs[1]["path"], topics[4]["path"], topics[5]["path"]],
    "web-tech/form-errors-and-recovery-paths": [topics[3]["path"], topics[6]["path"]],
    "web-tech/safe-file-upload-pipeline": [topics[7]["path"]],
    "web-tech/indexeddb-draft-queue": [topics[6]["path"]],
}
for path, targets in crosslinks.items():
    entry = by_path[path]
    entry["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": len(hubs), "new_lessons": len(topics)}))

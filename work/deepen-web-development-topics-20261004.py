"""Deepen the existing Web Development tracks and add integrated practice."""

import copy
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def link(path, label=None):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(label or by_path[path]["title"])}</a>'


def paragraph(value):
    return f"<p>{html.escape(value)}</p>"


# Each note adds an observable failure, a reproducible check, and a choice that
# differs from the introductory explanation already present on the lesson.
notes = {
    "component-boundaries-and-state": (
        "The note editor submits case 47, receives a timeout, and immediately shows a saved badge because the component copied its draft into the record list. A refresh removes the badge: the server never accepted the note. The user now has two conflicting accounts of the same action. Keep draft text and confirmed records separate; if optimistic display is intentional, label it pending and reconcile it with the response or a later read.",
        ["Submit with a rejected response and confirm the draft remains editable without appearing in the saved list.", "Open case 83 after editing case 47 and confirm the new editor has no inherited draft.", "Change one saved note and check that the derived count follows the current saved collection."],
        "A local form state is easier to reason about than a site-wide store for one editor. Move state outward only when independent views genuinely need one coordinated owner, and record which server response is allowed to replace that owner."),
    "browser-routing-and-history": (
        "A click handler calls pushState before its case fetch finishes. The network fails; the address bar now says case 47 while the screen still shows the list. Reloading that URL returns a server 404 because the route exists only inside client code. This is a route contract failure, not a rendering glitch. Serve the path directly, update history after the new view is ready, and preserve an ordinary anchor as the fallback.",
        ["Paste a case URL into a fresh tab and confirm the server returns useful HTML.", "Move Back and Forward twice after an in-page transition and compare both title and content with the URL.", "Force the API call to fail before navigation and confirm the anchor still reaches a valid page."],
        "A fast client transition is valuable only after direct navigation works. Keep route parameters in the URL and transient animation state in memory; storing whole page objects in history grows memory and creates stale copies."),
    "server-rendered-static-and-client-rendered-pages": (
        "The team moves a public guide into a blank client shell because the same component renders private cases. On a slow phone, the guide title appears after the bundle and data request; with scripts disabled it never appears. Meanwhile, one cache rule accidentally stores a private case response at a public edge. Split delivery by route: public guide HTML can be cached, while the private response needs request-time authorization and a private cache policy.",
        ["Fetch the initial guide document without executing scripts and inspect whether its main content is present.", "Request one private case as two users and confirm each response is authorized independently.", "Inspect cache headers on public and private routes separately, including a refresh after a write."],
        "Mixed rendering is often simpler than an all-or-nothing framework rule. Decide from the data and permission boundary first, then measure first useful content and interaction cost on the target device."),
    "locale-and-time-zone-boundaries": (
        "A report stores '04/10/26 09:20' without a zone. A reviewer in another country interprets it as a different day, and the export sorts that formatted string ahead of an earlier event. The ambiguity cannot be repaired from the display value alone. Store the event instant in an unambiguous form, keep an appointment's intended zone when future local time matters, and format only at the presentation boundary.",
        ["Format one stored instant in two time zones and confirm the underlying timestamp remains equal.", "Sort events across a month boundary by numeric instant, then compare the displayed order.", "Enter a local appointment during a daylight-saving transition and apply the product's explicit ambiguity rule."],
        "The selected locale changes punctuation and ordering conventions, while the selected zone changes wall time. Treat them as two inputs. Reuse one formatter for a long list instead of constructing it for every cell."),
    "cursor-pagination": (
        "Page one ends at inspection 93. A newer inspection is inserted before the user requests page two; offset pagination shifts the boundary and repeats a row. A cursor built only from created_at also fails when two records share that timestamp. Order by the timestamp and a unique ID, carry both values in the cursor, and hold filters constant for the traversal.",
        ["Insert a new newest row between page requests and check for repeated or missing IDs.", "Create two rows with the same timestamp and confirm the unique tie-breaker gives a total order.", "Try a malformed cursor and a changed reviewer filter; reject or restart the traversal explicitly."],
        "A cursor gives a position in a changing sequence, not a frozen snapshot. If a product needs a point-in-time export, define a snapshot or cutoff separately and test its retention cost."),
    "idempotent-write-requests": (
        "Two workers receive the same create request before either has written its in-memory key map. Both create an inspection, then both return success with different IDs. A lost response makes this race likely because the browser retries at exactly the uncertain moment. Reserve the key and commit the effect in one durable atomic boundary; bind the stored request fingerprint to the authenticated caller.",
        ["Send two concurrent requests with one key and assert both responses identify one stored record.", "Reuse the key with a changed body and assert a conflict without a new record.", "Drop the first response after commit, retry on another worker, and compare the returned record ID."],
        "A retry key should be scoped to one user intent and retained for a documented interval. After expiry, a delayed retry may create a second effect; expose that limit in the API contract instead of hiding it."),
    "background-jobs-and-outbox": (
        "The API returns 201 after saving inspection 93, but the process crashes before publishing its notification. The record exists; the reviewer never hears about it. Publishing before commit merely reverses the problem. Put the event instruction in the same transaction as the record, then let a worker deliver it. The worker still needs an idempotent downstream action because a crash can happen after delivery but before acknowledging the outbox row.",
        ["Crash after the transaction commits and verify the pending event remains available to a new worker.", "Deliver an event twice and confirm the recipient sees one effective notification.", "Pause the worker and alert on oldest pending event age rather than counting only API errors."],
        "An outbox narrows the database-to-queue gap; it does not guarantee exactly-once delivery to an external system. Report queued and delivered as different states so the interface matches reality."),
    "rate-limits-and-request-budgets": (
        "An office of 60 reviewers shares one gateway address. An IP-only export limit lets one busy reviewer exhaust the budget for everyone; a second failure appears when four app workers each permit three exports, multiplying the intended allowance. Use an authenticated subject and route cost as the key where possible, coordinate counters across instances, and cap the work of a single accepted request.",
        ["Issue the same caller's requests through two workers and confirm the shared limit stays fixed.", "Send requests from two users behind one address and check that one does not consume the other's allocation.", "Submit one oversized allowed export and verify body, query, and execution budgets still apply."],
        "A rejected response should state when a retry can make sense, without disclosing another account's usage. Observe rejection rates by endpoint and caller class before changing limits."),
    "canonical-route-identity": (
        "An old guide slug, a new category slug, and a query variant all return 200 with the same article. Internal links alternate between them, so updates and shares fragment across several identities. Choose the main route, redirect obsolete routes when practical, and keep canonical metadata aligned with the final URL. Do not point a genuinely different article at this route merely to consolidate signals.",
        ["Follow an old URL and confirm its redirect reaches the intended current page without a loop.", "Compare the canonical target with the final response URL and the links rendered in the page.", "Test a query variant that changes actual content; decide whether it is a distinct page."],
        "A canonical hint is weaker than a consistent site graph. Fix internal paths and server responses first, then use metadata to describe the same identity to automated readers."),
    "structured-data-visible-facts": (
        "The article says a case guide was updated this week, but its machine-readable date is hard-coded from an older fixture. Another field names an author absent from the page. The markup parses, yet it describes a different document. Build structured fields from the same validated content record used for visible title, author, and date; reject unsupported values rather than inventing them.",
        ["Compare every generated title, author, and date with what a reader can see on the page.", "Change the content record and confirm both HTML and structured fields update together.", "Render a page with missing author metadata and omit that property rather than filling a guessed name."],
        "Parsing success is only a syntax check. A publication review must check truthfulness, page type, and the rendered content because machine-readable data cannot compensate for a thin or misleading page."),
    "sitemap-and-index-control": (
        "A draft article lands in a sitemap before editors approve it. The route returns a preview to logged-in staff but a missing page to everyone else; another public guide is absent because the exporter reads an old route list. Generate discovery output from the same published-state source that serves public pages, and test the HTTP response for each listed path.",
        ["Assert every listed route is published and returns a public success response without credentials.", "Unpublish one page and confirm it leaves the next generated sitemap.", "Find published pages absent from the route inventory and decide whether they require discovery links."],
        "A sitemap can help discovery, but it does not make an isolated page useful. Keep category hubs and ordinary links aligned with the published route set so people can reach the same content."),
    "internal-link-architecture": (
        "A new lesson links only to the tutorial root, while three related lessons are buried behind search. The route exists and appears in the sitemap, yet a learner cannot move from a prerequisite to its application. Build a small relationship graph: prerequisite, next task, and sibling comparison. Use descriptive anchor text, then check that every link target still exists after a slug change.",
        ["Start at the subject root and traverse rendered lesson links to every published web lesson.", "Open a beginner lesson and confirm it offers a specific next step rather than a generic home link.", "Rename one route in a fixture copy and make link validation fail on the stale target."],
        "More links are not automatically better. Links should express a useful path through the material; a page of unrelated anchors increases choice cost without improving comprehension."),
    "service-worker-offline-fallback": (
        "A worker caches the login response under a broad path rule. After user A signs out, user B opens the site offline and sees user A's private case summary. An offline shell must not include account data from a previous session. Cache only explicitly public assets and a safe fallback page; let private responses follow a separate policy and clear account-bound local state on sign-out.",
        ["Load a public guide offline and verify a useful fallback or cached copy appears.", "Switch accounts on one browser profile and confirm no prior private response is served from storage.", "Install a new worker version and test how old caches are removed without breaking active tabs."],
        "A service worker intercepts requests but cannot manufacture current server truth. State what remains available offline and which operations are queued, blocked, or require a fresh authorization check."),
    "indexeddb-draft-queue": (
        "A reviewer writes a long note offline, closes the tab, and reopens it. The UI said 'saved' when it only updated an in-memory array; the note is gone. Persist a draft record and its sync state in a completed IndexedDB transaction before claiming local save. A queue item should include a stable client ID and the base server version so reconnect logic can detect duplicates and conflicts.",
        ["Write a draft, close the tab, reopen it offline, and confirm the exact text returns.", "Simulate a rejected storage transaction and ensure the interface does not announce a successful save.", "Replay the same queued item twice and verify the server does not create two notes."],
        "Local storage can be evicted or unavailable, so a local save is weaker than a server commit. Make that distinction visible and offer a way to export important unsynced work where the product requires it."),
    "web-app-manifest-and-install": (
        "The install prompt appears before the app has a useful offline path. A reviewer installs it, opens the case page without a connection, and gets a blank screen; the home shortcut also points to a private URL that requires a session. The manifest describes launch behavior and icons, but the underlying pages must work as ordinary web routes first. Choose a public start route and test it across sign-in states.",
        ["Open the declared start URL in a fresh browser profile before installation.", "Inspect each icon dimension and verify it renders at small and large launcher sizes.", "Launch the installed app after sign-out and offline; confirm both states explain the next action."],
        "Installation is an optional entry point, not evidence that the application is offline-capable. Keep browser navigation and accessible page content complete for users who never install anything."),
    "offline-sync-conflict-policy": (
        "Two reviewers edit the same case note from version 12. One saves online; the other reconnects with an offline draft and overwrites the newer text because the server accepted a blind update. Send the draft's base version with the write. On mismatch, preserve both versions and ask for a deliberate merge or choose a field-specific rule; never silently discard the unsynced work.",
        ["Create two drafts from one base version, commit one, then replay the other and expect a conflict.", "Verify the conflict response contains enough safe context to compare the two versions.", "Retry an unchanged queued request and ensure it cannot apply twice after a timeout."],
        "Last-write-wins can be reasonable for replaceable preferences. It is a poor default for substantive notes or records with audit requirements; the conflict rule should follow the value of the data."),
    "environment-config-and-secrets": (
        "A deployment embeds a service credential into a client bundle because the build system treats every environment variable as public. Anyone downloading the script can read it, and rotating the value requires a new release. Divide configuration by exposure: public flags may be baked into client code, while credentials stay on the server or in a secret store with narrow access.",
        ["Search built client assets for known secret canary values and fail the release if one appears.", "Boot a staging release with a missing required server secret and confirm it fails clearly before serving traffic.", "Rotate a credential and verify old instances stop using it within the planned interval."],
        "An environment name is not a security boundary. Review where a value is read, serialized, logged, and shipped, then give each deployed service only the credentials it needs."),
    "ci-release-gates": (
        "The pipeline reports green after unit tests, but the release serves a broken deep link because no check requests a nested route. Another change alters the database schema before the old app instances have drained. Add a small set of release gates that match real failure paths: build, contract tests, migration compatibility, direct-route smoke checks, and rollback readiness.",
        ["Run a production build and request a nested route as a fresh visitor.", "Deploy new and old app versions against the intermediate schema in a staging drill.", "Force one smoke check to fail and verify the release stops or rolls back as designed."],
        "A gate should catch a defined failure quickly enough to remain useful. Avoid a huge suite that no one trusts; keep the small critical path deterministic and investigate flaky checks as defects."),
    "horizontal-scale-and-shared-state": (
        "A session works on worker A and disappears on worker B. The team adds sticky routing, then a restart still loses every session because the state lives in process memory. Put cross-request state behind a shared store or a validated signed session design, and make handlers safe to run on any instance. Local caches can remain local if missing one changes speed rather than correctness.",
        ["Alternate requests between two instances and confirm the same authorized session is recognized.", "Restart one instance during a write and check that the committed result remains available.", "Expire a shared session and verify every instance rejects it without waiting for a local cache."],
        "Adding servers only helps if the bottleneck can be distributed. Measure database saturation, connection counts, and queue pressure before assuming more application processes increase throughput."),
    "backup-restore-drill": (
        "A backup job has run every night, but the only restore test uses an empty database. When a real incident occurs, the restored data lacks recent attachments and the application cannot start against the recovered schema. Rehearse a full restore into an isolated environment with representative records and media, then request key user flows and measure both data age and recovery time.",
        ["Restore into an isolated target and compare counts, selected IDs, and attachment checksums.", "Start the application against the restored schema and perform one authenticated read and write.", "Record the actual recovery time and newest restored record, then compare with the service promise."],
        "A backup artifact is evidence of copying bytes, not proof of recoverability. Keep restore credentials, retention, and runbook steps tested together; protect the drill environment from accidentally sending real notifications."),
    "relational-record-modeling": (
        "The API checks that a case exists before inserting an inspection, but another request deletes the case between those operations. The new inspection points to nothing. Express durable relationships and uniqueness in database constraints, then translate constraint failures into an API response. Application checks can improve error messages, but they cannot replace the database boundary under concurrency.",
        ["Attempt to insert an inspection for a missing case and confirm the database rejects it.", "Create two records with the same business key concurrently and confirm one wins without a duplicate.", "Delete or archive a parent record and verify the chosen retention rule for its children."],
        "Normalize records when it protects a real relationship and update path. A read-heavy projection can be added later; duplicated authoritative values require a reconciliation rule from day one."),
    "transactions-and-concurrent-writes": (
        "Two reviewers load case version 12, each changes its status, and both submit. Without a version condition, the second commit silently erases the first. A transaction makes a group of statements atomic, but it does not automatically express this business conflict. Use a conditional update on the expected version or an appropriate lock and report a conflict when no row is changed.",
        ["Run two writes using the same expected version and assert exactly one changes the record.", "Crash between two related statements and confirm neither partial state remains committed.", "Retry a serialization failure from the whole transaction boundary, not from one statement in isolation."],
        "Isolation level and locking choices affect contention. Start with the invariant to protect, measure conflicting writes, and choose the narrowest mechanism that preserves the promised result."),
    "indexes-and-query-plans": (
        "The feed query returns 25 rows in development but scans millions in production. A new index on created_at alone looks plausible, yet the query filters by reviewer and then orders by created_at plus ID. Inspect the actual plan with representative data and design an index for the filter and order together. An index that helps one read also adds space and write work.",
        ["Capture a plan for a large realistic reviewer feed, including estimated and actual row counts.", "Compare the page-one and deep-cursor query against the same index.", "Measure insert latency and index size after adding the candidate index."],
        "An execution plan is evidence for one workload, not a universal verdict. Recheck when distribution, filters, or ordering change, and avoid adding overlapping indexes merely because each query has a different name."),
    "expand-and-contract-migrations": (
        "A migration renames note_text while old app instances still write the previous column. Half the requests succeed and half fail during the rolling release. First add a compatible new column, then write and read across both versions while data is backfilled, and remove the old column only after old binaries are gone. Check the failure path in staging with both versions active.",
        ["Boot old and new application versions against the expanded schema at the same time.", "Backfill a partial batch, interrupt it, then resume without changing already migrated records incorrectly.", "Attempt the contract step while an old instance is still serving and ensure the release gate blocks it."],
        "Compatibility windows cost temporary code and storage. They are usually cheaper than downtime or data repair; keep the window short and observable rather than leaving two authoritative columns indefinitely."),
    "safe-file-upload-pipeline": (
        "A browser sends a file named inspection.jpg whose bytes are not an image. The server trusts the extension and serves the upload from the same origin as the application. A malicious payload can then reach users through a trusted route. Enforce size and type rules on the server, inspect the file content, store it outside executable paths, and generate safe derivatives before public delivery.",
        ["Upload a file with an image extension and non-image bytes; require rejection.", "Submit an oversized body and confirm it is stopped before expensive decoding or storage.", "Request the stored file as another user and verify authorization or public-access policy."],
        "Every accepted file has processing and storage cost. Quarantine or reject uncertain content, strip unneeded metadata where appropriate, and keep an audit trail from upload ID to generated variants."),
    "image-variants-and-delivery": (
        "A 4,000-pixel upload appears in a 180-pixel list card. The CSS shrinks it visually, but the browser still transfers and decodes the large source. Generate bounded variants and describe rendered sizes accurately; reserve intrinsic dimensions so layout remains stable. Inspect the crop manually when a detail in the photo matters for the case.",
        ["Record transferred bytes for a list page and a detail page at two viewport widths.", "Delay image loading and confirm surrounding text does not shift when the pixels arrive.", "Check the smallest crop for the inspection detail that the alt text says is visible."],
        "More variants increase storage and encoding work. Start with sizes tied to real display roles, then adjust from measured requests rather than generating every conceivable width."),
    "sse-and-websocket-choice": (
        "A team opens a WebSocket for a status label that changes once an hour. The connection infrastructure becomes the busiest part of the system, while a missed event still leaves the label stale. Start from the update contract: periodic polling may be enough; one-way events fit a frequent feed; two-way transport is justified when the browser must send live messages. In each case, a normal read supplies the starting state.",
        ["Disconnect the live channel and confirm the page still shows its last known state with a stale indicator.", "Reconnect after one missed update and compare with a fresh server snapshot.", "Measure open connections and per-event fan-out at the expected concurrent-reader count."],
        "Transport choice cannot replace event identity, authorization, or replay policy. State the freshness target first, then measure whether the simpler delivery method meets it."),
    "live-update-reconnect-and-order": (
        "The browser displays version 14, then a delayed event for version 13 arrives from another worker and overwrites it. After reconnect, the stream begins at version 17; versions 15 and 16 were missed. Compare versions before applying an event, and fetch a complete snapshot on a gap unless the server can replay a durable sequence.",
        ["Deliver versions 14, 13, and 15 out of order; the visible version must never move backward.", "Drop one event, reconnect, and confirm a snapshot or replay restores the current record.", "Reject an event for a different case even when its version number is higher."],
        "A timestamp is a weak ordering key when workers and client clocks differ. Use a server-owned sequence scoped to the record and document how long replay history is kept."),
}

broad_hubs = {
    "web-tech/frontend-application-architecture", "web-tech/backend-api-systems",
    "web-tech/data-persistence", "web-tech/media-and-live-updates",
    "web-tech/offline-and-device-capabilities", "web-tech/deployment-and-scale",
    "web-tech/content-discovery-and-structure",
}
broad_lessons = [entry for entry in entries if entry["type"] == "article" and entry["data"].get("section_path") in broad_hubs]
assert len(broad_lessons) == 28 and len(notes) == 28
for entry in broad_lessons:
    slug = entry["path"].split("/")[-1]
    failure, checks, decision = notes[slug]
    assert len(checks) == 3
    entry["body"] += "<h2>Failure trace</h2>" + paragraph(failure)
    entry["body"] += "<h2>Verification</h2><ul>" + "".join(f"<li>{html.escape(check)}</li>" for check in checks) + "</ul>"
    entry["body"] += "<h2>Decision note</h2>" + paragraph(decision)
    entry["updated_at"] = stamp
    prose = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<pre>.*?</pre>", " ", entry["body"], flags=re.S)))
    entry["data"]["reading_minutes"] = max(6, round(len(re.findall(r"\b[\w'-]+\b", prose)) / 155))


projects = [
    dict(path="web-tech/paginated-inspection-feed-project", title="Project: paginated inspection feed with safe writes",
         summary="Build a reviewer feed that survives new rows, duplicate requests, and concurrent updates.",
         intro="Build a small inspection feed for reviewer 29. The first page lists at most 25 cases in descending creation order, with the record ID breaking timestamp ties. A create form writes a new inspection through a server endpoint; a repeated request with the same key must return the first result. Keep the interface usable when its optional fetch layer fails.",
         scope=["Model case and inspection records with database constraints, then expose a bounded read endpoint whose cursor encodes both ordered fields.", "Accept a caller-scoped idempotency key on creation, store its request fingerprint with the result, and reject a changed body under the same key.", "Render a server-readable first page and use a real form action. Enhance pagination only after direct navigation and keyboard submission work."],
         code="SELECT inspection_id, created_at, summary\nFROM inspections\nWHERE reviewer_id = :reviewer_id\n  AND (created_at, inspection_id) < (:cursor_time, :cursor_id)\nORDER BY created_at DESC, inspection_id DESC\nLIMIT :page_limit;",
         language="sql", cost="An indexed page read seeks near the cursor and returns O(P) rows for page size P; an unbounded export has different cost and needs its own budget. The idempotency record adds storage and a transactional write. Test with tied timestamps and a new row inserted between page requests.",
         failures=["The same row appears on two pages after a new insertion.", "A lost create response produces two inspections after retry.", "A cursor from another reviewer exposes records outside the caller's scope."],
         accept=["Page through 53 seeded inspections and compare unique IDs with the authorized set.", "Race two identical create requests on separate workers and confirm one persisted inspection.", "Open the second-page URL directly, then disable scripts and submit the create form."],
         related=["web-tech/cursor-pagination", "web-tech/idempotent-write-requests", "web-tech/relational-record-modeling", "web-tech/browser-routing-and-history", "web-tech/record-level-authorization"]),
    dict(path="web-tech/offline-photo-intake-project", title="Project: offline inspection draft and photo intake",
         summary="Keep a draft through disconnects, then reconcile its version and safely process a photo.",
         intro="Build an inspection note editor that can survive a tab close while offline. Store the draft with a stable local ID and the server version from which it began. On reconnect, submit the note through a write contract that can report a conflict. Treat the attached photo as an untrusted upload; the server must validate and convert it before the case page serves a bounded variant.",
         scope=["Persist draft text and sync state in IndexedDB and distinguish local save from server commit in the status region.", "Send the base record version with the write and preserve both copies when a concurrent edit creates a conflict.", "Limit upload size, inspect content rather than the filename, and deliver separate card and detail image variants with dimensions."],
         code="function classifyDraft(serverVersion, draftBaseVersion) {\n  if (serverVersion !== draftBaseVersion) return 'resolve conflict';\n  return 'commit draft';\n}\nconsole.log(classifyDraft(14, 12));",
         language="javascript", cost="A local draft write is O(B) in draft bytes; upload transfer and image conversion dominate for a photo of M bytes and its variants. Quota and eviction make local storage a temporary safety net, so the interface must never label an unsynced draft as a confirmed server record.",
         failures=["The UI reports success before the local transaction finishes and loses the note on tab close.", "A reconnect overwrites an online edit without showing a conflict.", "A renamed non-image file is served as trusted content."],
         accept=["Write a note, go offline, close the tab, reopen it, and recover the exact text.", "Commit an online change elsewhere, reconnect, and confirm the draft remains available for comparison.", "Upload mismatched and oversized files, then inspect card image bytes and reserved layout space."],
         related=["web-tech/indexeddb-draft-queue", "web-tech/offline-sync-conflict-policy", "web-tech/safe-file-upload-pipeline", "web-tech/image-variants-and-delivery", "web-tech/accessible-feedback-and-keyboard"]),
    dict(path="web-tech/live-review-board-project", title="Project: live review board with ordered status",
         summary="Show current case state, then apply only authorized and newer events.",
         intro="Build a review board that renders its current state in initial HTML and then receives status changes. Choose a one-way event stream if the browser only reads updates; use a two-way channel only if active collaboration needs it. Every event carries a case ID and a server-owned version. A gap after reconnect triggers a snapshot read before the board claims to be current.",
         scope=["Render an authorized case snapshot through an ordinary route, with status text available before live code starts.", "Validate the case ID and version on every event, discard stale events, and recover from gaps using a current snapshot.", "Close unused streams, bound the number of active connections, and show a stale status when the feed disconnects."],
         code="let visibleVersion = 12;\nfunction receiveStatus(event) {\n  if (event.caseId !== 47 || event.version <= visibleVersion) return 'ignore';\n  if (event.version !== visibleVersion + 1) return 'load snapshot';\n  visibleVersion = event.version;\n  return 'apply';\n}\nconsole.log(receiveStatus({ caseId: 47, version: 14 }));",
         language="javascript", cost="Each event comparison is O(1), but fan-out to C readers can require O(C) delivery work and C open connections. A snapshot fetch on gaps adds network cost but prevents a convincing display of incomplete state. Measure connection count and queue delay under load.",
         failures=["A delayed old event rolls the visible status backward.", "A reconnection skips an event yet the UI still says current.", "An event for another case updates the active case panel."],
         accept=["Deliver versions 14, 13, then 15 from a starting version of 12 and inspect the resulting state.", "Disconnect through a missed update and require a snapshot or replay before clearing the stale label.", "Open and close many board tabs and confirm server connection counts return to baseline."],
         related=["web-tech/sse-and-websocket-choice", "web-tech/live-update-reconnect-and-order", "web-tech/record-level-authorization", "web-tech/accessible-feedback-and-keyboard", "web-tech/horizontal-scale-and-shared-state"]),
    dict(path="web-tech/release-recovery-drill-project", title="Project: release and recovery drill for a content service",
         summary="Stage a schema change, direct-route smoke check, backup restore, and rollback decision.",
         intro="Take a small content service through a controlled release. Add a new article field without breaking the old application version, deploy the new version while both are active, and remove the old field only after compatibility is proven. In a separate isolated target, restore a representative backup and request the restored routes. Record what worked and how long recovery took.",
         scope=["Use an expand, backfill, switch, and contract migration sequence with an explicit old-version compatibility check.", "Gate release on a production build, a deep-link response, an authenticated read, and a bounded write.", "Restore database and media into isolation, disable outbound notifications, and compare recovered data age with the service promise."],
         code="set -eu\n: \"${DEPLOY_BASE_URL:?set the deployment origin}\"\ncurl --fail --silent --show-error \"$DEPLOY_BASE_URL/cases/47\" | grep -F 'Case 47'\ncurl --fail --silent --show-error \"$DEPLOY_BASE_URL/guides/inspection-notes\" | grep -F 'Inspection notes'",
         language="bash", cost="The gate adds minutes to a release and the dual-schema window temporarily adds storage and write paths. A restore drill consumes isolated compute and operator time; it also replaces guesswork with measured recovery time and data age. Run the expensive drill on a schedule appropriate to the service, while the small route smoke remains part of each release.",
         failures=["The old binary fails while the new schema is live.", "A nested article route works only after client-side navigation.", "Database records restore but their referenced images are absent."],
         accept=["Keep old and new binaries active against the expanded schema and complete one write from each.", "Request a nested published article URL as a fresh client and compare the returned title with the route record.", "Restore an isolated backup, verify selected content and media checksums, and document recovery time."],
         related=["web-tech/expand-and-contract-migrations", "web-tech/ci-release-gates", "web-tech/backup-restore-drill", "web-tech/canonical-route-identity", "web-tech/sitemap-and-index-control"]),
]

for number, project in enumerate(projects, start=1):
    assert project["path"] not in by_path
    entry = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
                 path=project["path"], title=project["title"], summary=project["summary"],
                 sort_order=960 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                     "content_format": "html", "seo_ready": False, "kind": "project",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8,
                     "related": project["related"]}
    body = paragraph(project["intro"])
    body += "<h2>Build contract</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["scope"]) + "</ul>"
    body += f'<h2>Implementation checkpoint</h2><pre><code class="language-{project["language"]}">{html.escape(project["code"], quote=False)}</code></pre>'
    body += "<h2>Cost and boundaries</h2>" + paragraph(project["cost"])
    body += "<h2>Acceptance checks</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["accept"]) + "</ul>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["failures"]) + "</ul>"
    body += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
    entry["body"] = body
    entries.append(entry)
    by_path[entry["path"]] = entry

project_hub = by_path["web-tech/web-technology/project"]
project_hub["summary"] = "Build and verify seven projects across browser, API, data, offline, live, and release contracts."
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Integrated projects</h2><ul>" + "".join(
    f'<li>{link(project["path"])} — {html.escape(project["summary"])}</li>' for project in projects) + "</ul>"
project_hub["updated_at"] = stamp


quiz_specs = [
    dict(path="quizzes/web-development-data-and-api-contracts", title="Web Development: data and API contracts quiz",
         summary="Twelve explained questions on pagination, retries, transactions, indexes, and release-safe schema changes.",
         related=["web-tech/cursor-pagination", "web-tech/idempotent-write-requests", "web-tech/background-jobs-and-outbox", "web-tech/transactions-and-concurrent-writes", "web-tech/indexes-and-query-plans", "web-tech/expand-and-contract-migrations"],
         questions=[
             ("A newer row arrives before a reviewer asks for page two. Which scheme avoids offset shift?", ["A cursor using the ordered timestamp and unique ID", "A larger fixed offset", "Sorting only by timestamp"], 0, "The ordered pair marks the last seen position. A new row at the front does not change that position, while an offset can repeat or skip a record."),
             ("What must the server do with a cursor from another reviewer's feed?", ["Trust the encoded reviewer ID", "Apply the current caller's authorization and filters again", "Return all rows after the cursor"], 1, "A cursor is a position marker, not permission. Every page request must apply the caller's visibility rule and validate the cursor's context."),
             ("A create request commits but its response is lost. What should an identical retry return?", ["A second new record", "A generic 500 response", "The first committed result"], 2, "A durable idempotency record binds the retry key and request fingerprint to the original result, so uncertain transport does not duplicate the effect."),
             ("The same idempotency key arrives with changed input. What response fits the contract?", ["A conflict without repeating the write", "The old result for the new input", "A second write under the old key"], 0, "The key identifies one user intent. Reusing it for a different body must be rejected so the caller cannot mistake an earlier result for the changed request."),
             ("Why store an outbox event with the business row in one transaction?", ["To make external delivery exactly once", "To keep the instruction durable if the process crashes after commit", "To avoid all worker retries"], 1, "The transaction prevents a committed business record from losing its follow-up instruction in the gap before a separate publish step."),
             ("A worker sent a notification but crashed before acknowledging the event. What is required?", ["Delete the business record", "Assume the event was never delivered", "A downstream deduplication or reconciliation rule"], 2, "The worker may retry after an uncertain acknowledgement. External effects need a stable event identity or another rule that makes repeat delivery safe."),
             ("Two users update version 12 concurrently. What prevents a silent lost update?", ["An expected-version condition on the write", "A client timestamp in the button label", "A longer HTTP timeout"], 0, "A conditional write changes the record only if its current version still matches the editor's base version; otherwise the client receives a conflict."),
             ("What should a relational database enforce for a required parent case?", ["A CSS required selector", "A foreign-key relationship or equivalent database constraint", "Only a pre-insert browser lookup"], 1, "The database constraint closes the race between an application existence check and a concurrent delete or update of the parent row."),
             ("A filtered feed sorts by created_at and inspection_id. What is a useful index investigation?", ["Add an index on every column independently", "Ignore production row distribution", "Inspect a plan for the filter plus ordered pair on representative data"], 2, "A query plan with realistic data shows whether an index supports the actual filter and order; individual indexes may not provide the desired traversal."),
             ("What is the first step when renaming a column during a rolling release?", ["Add a compatible new shape while old code still works", "Drop the old column immediately", "Deploy only the frontend"], 0, "The expand stage gives old and new binaries a shared compatible schema before backfill and traffic switching; contracting early breaks old instances."),
             ("What does a rate limit fail to replace?", ["A route budget", "Authorization and per-request resource limits", "A retry hint"], 1, "Limiting request frequency does not decide which records a caller may access or prevent one allowed request from consuming excessive work."),
             ("What must a project test after a retry key's retention window expires?", ["Only the CSS response", "Whether timestamps sort lexically", "Whether a delayed retry can produce a second effect"], 2, "Expiry bounds storage but also weakens deduplication for very late retries. The documented API contract and tests must expose that limit."),
         ]),
    dict(path="quizzes/web-development-offline-delivery-contracts", title="Web Development: offline and delivery contracts quiz",
         summary="Twelve explained questions on drafts, conflicts, uploads, live events, release gates, and discovery.",
         related=["web-tech/indexeddb-draft-queue", "web-tech/offline-sync-conflict-policy", "web-tech/safe-file-upload-pipeline", "web-tech/live-update-reconnect-and-order", "web-tech/backup-restore-drill", "web-tech/internal-link-architecture"],
         questions=[
             ("When may a draft UI claim a local save succeeded?", ["After assigning an in-memory variable", "After its storage transaction completes", "Before the user types"], 1, "The browser can close after a memory-only update. A completed storage transaction is the boundary for a local save claim, though it is still not a server commit."),
             ("An offline draft began at version 12; the server is now at version 14. What is the safe next step?", ["Show a conflict and preserve both versions", "Overwrite the server immediately", "Delete the local draft"], 0, "A base-version mismatch means another write happened. Preserving both values lets the user or a field-specific merge rule resolve the difference."),
             ("What should an offline service worker avoid caching across accounts?", ["Public static assets", "A safe fallback page", "Private case responses without an account-bound policy"], 2, "A broad private-response cache can show one person's data to the next user of the same browser profile. Offline assets need an explicit exposure policy."),
             ("Does a valid web app manifest prove useful offline behavior?", ["Yes, installation supplies server data", "No, the app still needs real offline routes and state rules", "Yes, icons cache all pages"], 1, "A manifest describes launch behavior and appearance. It does not supply current private data, a safe offline fallback, or synchronization rules."),
             ("A file is named photo.jpg but contains unrelated bytes. What should the server use?", ["Server-side size and content checks before processing", "The filename extension alone", "Only the browser accept attribute"], 0, "Client hints and extensions are untrusted. The upload boundary must inspect content, bound work, and store the result in a safe delivery path."),
             ("Why generate a 180-pixel card variant from a large image?", ["To replace authorization", "To make alt text optional", "To reduce transfer and decode work for that display role"], 2, "CSS shrinking changes display size but not the bytes fetched or pixels decoded. A bounded variant better matches the card's actual role."),
             ("A read-only status board updates once an hour. Which transport should be considered first?", ["A two-way socket regardless of cost", "Simple polling against the freshness target", "No initial server read"], 1, "When updates are rare, periodic reads may meet the freshness requirement with less connection overhead. Transport follows the product's timing contract."),
             ("The board shows version 14 and receives version 13. What should it do?", ["Discard the stale event", "Apply it because it arrived later", "Reset to version 1"], 0, "A server-owned version expresses record order. Arrival order after retries or across workers can differ and must not move visible state backward."),
             ("A stream reconnects at version 17 after version 14 was visible. What restores confidence?", ["Changing the clock display", "Hiding the gap", "Replaying retained events or fetching a current snapshot"], 2, "The client missed changes. A complete snapshot or durable replay is needed before claiming the displayed state is current."),
             ("What proves that a backup can recover a content service?", ["A successful copy job only", "An isolated restore with representative data and route checks", "A filename ending in .bak"], 1, "A rehearsal checks schema, data, media, credentials, and real application behavior; copying bytes alone does not prove recovery."),
             ("What should a sitemap generator use as its route source?", ["The same published-state inventory serving public pages", "Every draft in the editor", "Only the browser's current URL"], 0, "Public discovery output must agree with what anonymous readers can request. Drafts and stale route lists create broken or misleading entries."),
             ("What makes internal links useful in a technical curriculum?", ["Linking every word to the home page", "Adding unrelated anchors until the page is long", "Connecting prerequisites, next tasks, and closely related comparisons"], 2, "A deliberate path helps readers move through concepts and practice. Link counts alone do not indicate a useful learning structure."),
         ]),
]

for number, spec in enumerate(quiz_specs, start=1):
    assert spec["path"] not in by_path
    entry = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + spec["path"])),
                 path=spec["path"], title=spec["title"], summary=spec["summary"],
                 sort_order=990 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                     "content_format": "html", "seo_ready": False,
                     "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                                   for prompt, options, answer, explanation in spec["questions"]]}
    entry["body"] = paragraph(spec["summary"] + " Choose an answer, inspect its reason, then reopen the linked lesson for the failed boundary.")
    entry["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in spec["related"]) + ".</p>"
    entries.append(entry)
    by_path[entry["path"]] = entry

quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].extend(spec["path"] for spec in quiz_specs)
quiz_hub["body"] += "<h2>Broader contract checks</h2><ul>" + "".join(
    f'<li>{link(spec["path"])} — {html.escape(spec["summary"])}</li>' for spec in quiz_specs) + "</ul>"
quiz_hub["updated_at"] = stamp

project_by_theme = {
    "web-tech/frontend-application-architecture": projects[0]["path"],
    "web-tech/backend-api-systems": projects[0]["path"],
    "web-tech/data-persistence": projects[0]["path"],
    "web-tech/media-and-live-updates": projects[2]["path"],
    "web-tech/offline-and-device-capabilities": projects[1]["path"],
    "web-tech/deployment-and-scale": projects[3]["path"],
    "web-tech/content-discovery-and-structure": projects[3]["path"],
}
quiz_by_theme = {
    "web-tech/frontend-application-architecture": quiz_specs[1]["path"],
    "web-tech/backend-api-systems": quiz_specs[0]["path"],
    "web-tech/data-persistence": quiz_specs[0]["path"],
    "web-tech/media-and-live-updates": quiz_specs[1]["path"],
    "web-tech/offline-and-device-capabilities": quiz_specs[1]["path"],
    "web-tech/deployment-and-scale": quiz_specs[1]["path"],
    "web-tech/content-discovery-and-structure": quiz_specs[1]["path"],
}
for entry in broad_lessons:
    theme = entry["data"]["section_path"]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_by_theme[theme]) + "; then check the boundary with " + link(quiz_by_theme[theme]) + ".</p>"
    entry["data"]["related"].extend([project_by_theme[theme], quiz_by_theme[theme]])

for theme in broad_hubs:
    entry = by_path[theme]
    entry["body"] += "<h2>Practice path</h2><p>After the four lessons, build " + link(project_by_theme[theme]) + " and take " + link(quiz_by_theme[theme]) + ".</p>"
    entry["updated_at"] = stamp

root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Integrated practice</h2><p>Use " + link("web-tech/web-technology/project") + " to apply the track, then check decisions in " + link("web-tech/quizzes") + ".</p>"
root_entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"deepened_lessons": len(broad_lessons), "new_projects": len(projects),
                  "new_quizzes": len(quiz_specs), "new_questions": sum(len(spec["questions"]) for spec in quiz_specs)}))

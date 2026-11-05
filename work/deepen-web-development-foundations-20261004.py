"""Deepen the original browser-to-release lessons without changing the topic map."""

import datetime
import html
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def para(value):
    return f"<p>{html.escape(value)}</p>"


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


notes = {
    "http-request-response-contract": (
        "A dashboard sends GET to a path named create-inspection and the server writes a row. A browser prefetch or an automated checker can now create records without anyone pressing Save. The route name does not alter the method's meaning. Move the mutation to a write method, validate its body and permission, and return a status that matches the committed effect. On failure, the client must not infer success merely because a JSON object arrived.",
        ["Issue the read endpoint twice and assert the record count never changes.", "Send a blank write body and verify both the error status and unchanged storage.", "Simulate a successful write response being lost, then document how a retry avoids a duplicate."],
        "A 4xx response is an observed server decision, while a transport failure has no response to inspect. Keep these branches separate in logs and UI; the recovery action for missing data differs from the action for a dropped connection."),
    "url-origin-and-query-boundary": (
        "A search term contains an ampersand and a hash mark. The client concatenates raw text into a URL; half the term becomes another parameter, and the rest is treated as a fragment that never reaches the server. Another developer stores an access token in the query for convenience, leaving it in browser history and logs. Use a URL parser and URLSearchParams, then validate the resulting field again on the server.",
        ["Submit a term containing ampersand, hash, plus, and non-ASCII text; compare the server's received value.", "Change only the fragment and confirm the request target does not change.", "Open the same host on a different port and confirm the browser treats it as another origin."],
        "A query is useful for bookmarkable reads and filters. It is a poor place for secrets or a large mutable draft. The server must treat every query value as caller-controlled even when client code generated it."),
    "dns-tls-and-first-connection": (
        "A case page fails before any HTTP response is received. The team adds a retry to JSON parsing, but the real fault is a stale DNS record or a certificate whose name does not match the requested host. Trace the connection in stages: name lookup, network connection, TLS verification, request, then response. A page-level 404 is a different failure because an HTTP server answered.",
        ["Request the same path by its normal host and record whether an HTTP status arrives.", "Test a certificate-name mismatch and confirm the client stops before sending application credentials.", "Change a DNS answer in a staging drill and observe connection behavior until cached answers expire."],
        "DNS and TLS add work to a cold connection; reused connections can amortize it across requests. Treat a certificate warning as a connection-integrity failure, not an invitation to add a bypass in application code."),
    "route-parameters-and-error-responses": (
        "The server parses /cases/47 as an integer but accepts /cases/47notes by reading only the initial digits. A second route returns the same 404 for an unknown case and a database outage, so the client offers a misleading 'create case' action during an incident. Match the whole route parameter, validate its shape, and distinguish missing resources from unavailable dependencies without exposing internals.",
        ["Request a valid ID, a malformed suffix, and an ID that has no record; compare status and body shape.", "Disable the database and verify the route does not pretend the record is absent.", "Request another user's valid case and confirm the disclosure policy does not expose its details."],
        "A path parameter selects a candidate resource; it does not grant access. Parse first, authenticate and authorize next, then read or mutate within the service's error contract."),
    "browser-parse-load-and-render": (
        "A page ships a useful case title only in a late API response. The server returns 200 immediately, so a synthetic response-time check looks healthy, but a slow browser shows an empty main region while scripts download and execute. Put essential case text in the initial HTML, defer dependent enhancement, and reserve the image box. Inspect the rendered state, not just the network waterfall's first line.",
        ["Disable scripts and verify the case title, status, and navigation are still readable.", "Throttle script delivery and observe when the first meaningful text becomes visible.", "Delay the main image and confirm declared dimensions prevent nearby text from moving."],
        "The request critical path includes transfer, parsing, style calculation, layout, and script work. Reducing one response's size may not improve the page if a blocking dependency remains ahead of useful content."),
    "dom-events-progressive-enhancement": (
        "A search works when the button is clicked but fails when the user presses Enter. Its script listens to click on one button, then cancels navigation before it knows whether the API is available. Keep a real form action and handle submit, which covers both keyboard and pointer activation. If the enhanced request fails, let the browser follow the form's normal route with the entered values intact.",
        ["Submit the same query with Enter and the button; compare the resulting request.", "Disable JavaScript and confirm the native form still reaches useful results.", "Make the enhanced fetch fail and confirm the fallback does not erase the entered term."],
        "One stable form handler is usually enough. Event delegation helps when controls are inserted later, but it does not excuse vague target checks or replacing semantic controls with clickable text."),
    "fetch-status-and-abort": (
        "A reviewer searches pump, then valve. The older pump request finishes last and overwrites the newer valve results. A different path treats a received 404 as a network exception because code assumes fetch rejects on error status. Abort obsolete reads, track which query owns the display, and inspect response.ok before decoding a success representation. A timeout on a write remains uncertain; cancellation cannot prove the server did nothing.",
        ["Delay the first search response behind the second and ensure it never updates the final view.", "Return 404 and 500 responses separately from a rejected network request; verify distinct UI states.", "Cancel a write after it reaches the server and verify the client does not promise that storage is unchanged."],
        "Aborting can save browser work, yet the server may still finish. For read-only searches, stale-result suppression is enough; for writes, pair retries with an idempotent server contract."),
    "form-server-validation": (
        "A browser field has required and maxlength, so the team skips server checks. A direct HTTP client submits a whitespace-only note of 4,000 characters, and it reaches storage. Browser constraints improve interaction but cannot protect the database. Parse and bound the request body, validate field rules server-side, then return field-specific errors while preserving safe values the person already entered.",
        ["Submit an empty note through the browser and through a direct request; both must be rejected.", "Send a body beyond the configured size limit and confirm it is stopped before storage work.", "Return two field errors and verify their messages are connected to the controls and focus path."],
        "Validation rules belong where the trusted write happens. Duplicate a small subset in the browser for fast feedback, but keep the server rule authoritative and version it with the API contract."),
    "cors-and-cross-origin-requests": (
        "A frontend on one origin cannot read an API response from another, so a developer sets a wildcard allow-origin value while also expecting cookies to travel. The browser rejects that combination; worse, the team mistakes the CORS header for an authorization decision. Allow only the intended origins with the right credential policy, and still authenticate and authorize each endpoint on the server.",
        ["Call the API from the intended frontend origin and an unapproved origin; compare browser access.", "Exercise a credentialed request and inspect both preflight and actual response headers.", "Send a direct server-side request without an Origin header and confirm permission checks still apply."],
        "CORS controls whether browser script can read a cross-origin response. It is not a firewall for the endpoint: non-browser clients can call the server, so every protected resource needs its own access check."),
    "responsive-interaction-contract": (
        "A filter panel fits on a wide monitor but becomes a fixed overlay on a narrow phone. The Apply button falls below the viewport, and keyboard focus moves behind the overlay. Shrinking text does not repair the interaction. Let controls reflow in source order, test touch targets and focus, and ensure the same task can finish at narrow widths without horizontal scrolling.",
        ["Complete the case filter at a narrow viewport using only keyboard navigation.", "Increase text size and confirm labels and buttons remain visible without clipping.", "Open and close the panel on a touch device and check that focus returns to the trigger."],
        "Responsive behavior is a task contract, not a screenshot width. Fewer columns can reduce layout complexity, but hiding essential controls behind several taps adds interaction cost that needs user testing."),
    "session-cookie-and-csrf-boundary": (
        "A signed-in browser automatically attaches its session cookie to a forged write request initiated from another page. The server checks only that the cookie is valid and records the attacker's chosen note. Bind the mutation to a CSRF defense suited to the session design, check the request's intended origin where appropriate, and keep the session reference out of script-readable storage when possible.",
        ["Submit an authenticated write without the expected CSRF proof and confirm rejection.", "Try the same request with a valid proof and verify the stored result and response status.", "Sign out, replay the old cookie, and confirm the server no longer recognizes that session."],
        "Cookie flags narrow exposure but do not replace a complete write defense. Session validation, request intent, and record-level permission are separate checks that all matter before storage changes."),
    "browser-storage-boundary": (
        "A page stores the latest case note and bearer token beside a theme preference in localStorage. A script injected through an unrelated widget reads both, and a shared browser later reveals the old note to another person. Keep only low-risk convenience state in browser storage, validate its shape on read, and let the server hold authoritative records and session state.",
        ["Seed an unexpected stored value and confirm the page falls back without crashing.", "Block storage writes and verify the control remains usable for the current visit.", "Sign out and confirm account-bound local data is removed or becomes inaccessible by policy."],
        "Storage APIs are synchronous or quota-bound in ways that vary by browser. Treat them as convenience caches and drafts with explicit loss and privacy rules, not as an invisible database."),
    "cache-etag-revalidation": (
        "The browser shows an old case after an update because the response was treated as fresh for too long. The team then disables every cache, increasing transfer without fixing the private-data policy. Give representations an appropriate cache rule and validator; a stale client can send If-None-Match and receive 304 when the current representation is unchanged, or 200 with a new body when it changed.",
        ["Read a case, repeat with its validator, and confirm an unchanged response omits the full body.", "Change the record, repeat the conditional request, and confirm the new representation arrives.", "Use two accounts and verify a private cached response is never shared across them."],
        "A validator avoids retransmitting unchanged bytes but still costs a request and server comparison. Choose freshness duration, privacy policy, and invalidation from the data contract rather than applying one setting to all pages."),
    "output-escaping-and-csp": (
        "A case title contains markup-like text. A developer inserts it through innerHTML, turning a stored value into browser instructions; adding a restrictive policy later reduces some impact but does not make the unsafe insertion correct. Use a text sink for text, context-appropriate escaping for generated HTML, and a policy that limits script execution as another layer.",
        ["Store text containing angle brackets and quotes, then verify it renders as text in every view.", "Exercise an attribute and a URL context separately; do not reuse an HTML-text escape as a universal rule.", "Deploy the policy in a reporting stage and inspect violations before enforcing it."],
        "The cheapest defense is to avoid parsing untrusted strings as markup. A content policy can reduce damage and reveal mistakes, but maintaining nonces and allowed resources has operational cost."),
    "record-level-authorization": (
        "Reviewer 29 may view case 47 but not case 83. The UI hides case 83's link, yet a direct request to /cases/83 returns its details because the handler only checked that the reviewer was signed in. Filter by the authenticated user's assignment on every read and write, including nested notes and media. Never trust the case ID sent by the browser as proof of permission.",
        ["Request an assigned case and an unassigned case with the same signed-in session.", "Change only the path ID in a write request and verify the protected record remains unchanged.", "Load a child attachment through its direct URL and confirm its parent permission is enforced."],
        "A fast permission lookup may be cached, but a stale cache can extend access after revocation. Decide the acceptable delay explicitly and test it during reassignment and sign-out."),
    "accessible-feedback-and-keyboard": (
        "A submission fails validation, but errors appear only as red borders. A keyboard user remains at the submit button with no indication of which field needs work; a screen reader gets no status change. Return field errors, connect them to their controls, and move focus to a useful summary or first invalid control. Keep success and loading text in an existing status region.",
        ["Submit with two invalid fields using only the keyboard and locate both messages without guessing.", "Inspect the input's accessible name and error description after failure.", "Trigger a successful save and confirm the status is announced without unexpectedly moving focus."],
        "An announced status should describe the state change briefly. Repeated or assertive announcements can interrupt other work; use the least disruptive behavior that still makes the result available."),
    "performance-budget-and-layout-stability": (
        "A page's HTML arrives quickly, yet a large client bundle delays its first useful content and an image without dimensions shifts the Save button while someone is about to press it. Set budgets for the actual user path: initial text, input readiness, transfer, and layout stability. Measure a slow device and narrow viewport, then remove or defer the dependency causing the delay.",
        ["Throttle CPU and network, reload, and record when the title is readable and the form responds.", "Delay the largest image and verify that the form's position stays stable.", "Compare bundle and image transfer before and after one targeted change, including cache-cold load."],
        "A budget is a decision trigger, not a decorative score. Keep it tied to the route and device class; one aggregate number can conceal a slow critical page."),
    "contract-tests-across-boundaries": (
        "A server changes a validation response from fieldErrors to errors. Its unit tests pass, and the browser silently shows 'Something went wrong' because it expects the old field. Test a small set of request and response shapes across the actual boundary, including status, error fields, permission, and the success body. A mock that repeats the frontend's assumption cannot catch this drift.",
        ["Send a valid write and an invalid write to the server contract, checking status and response fields.", "Run the browser against a deliberate changed error shape and verify a contract check fails.", "Exercise a direct nested route on the built release, not only a client transition."],
        "Contract tests are most useful at stable seams. Keep them focused on externally observable behavior; implementation-detail assertions make safe refactoring costly without protecting the user."),
    "observability-and-recovery": (
        "A write returns 500 for one reviewer, but the logs record only 'request failed' with no request ID, route, or stage. The operator cannot tell whether validation, database commit, or notification delivery failed; retrying blindly may duplicate work. Emit a safe correlation ID and structured stage outcome, then expose an error state that tells the user whether a retry is safe.",
        ["Trace one request ID from browser error to server route and storage outcome.", "Force a post-commit notification failure and confirm the record and pending work are visible separately.", "Check that logs omit note text, credentials, and other sensitive payloads."],
        "More logging is not the goal. Record enough to distinguish failure classes, bound retention, and connect alerts to a recovery action that an operator can actually perform."),
    "release-smoke-and-rollback": (
        "The homepage passes a smoke check, but a nested case URL returns a server 404 after deployment. A new database migration also makes the old application binary unusable, so a code rollback cannot restore service. Smoke-check a direct critical route and an authorized data path, and prove schema compatibility before release. A rollback plan must match the actual state already written.",
        ["Request a nested page directly in a clean session after deployment.", "Run one authenticated read and a controlled write against the released service.", "Start the previous binary against the migrated schema in staging before calling rollback ready."],
        "A smoke check is intentionally small and fast. It catches obvious route and contract failures; broader accessibility, performance, and data recovery require separate gates and drills."),
}

foundation_sections = {
    "web-tech/request-and-browser-foundations", "web-tech/browser-interactions",
    "web-tech/state-and-trust", "web-tech/quality-and-release",
}
foundation = [entry for entry in entries if entry["type"] == "article" and entry["data"].get("section_path") in foundation_sections]
assert len(foundation) == 20 and len(notes) == 20
for entry in foundation:
    slug = entry["path"].split("/")[-1]
    failure, checks, decision = notes[slug]
    assert len(checks) == 3
    entry["body"] += "<h2>Failure trace</h2>" + para(failure)
    entry["body"] += "<h2>Verification</h2><ul>" + "".join(f"<li>{html.escape(check)}</li>" for check in checks) + "</ul>"
    entry["body"] += "<h2>Decision note</h2>" + para(decision)
    entry["updated_at"] = stamp
    prose = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<pre>.*?</pre>", " ", entry["body"], flags=re.S)))
    entry["data"]["reading_minutes"] = max(6, round(len(re.findall(r"\b[\w'-]+\b", prose)) / 155))


entry = by_path["web-tech/getting-started"]
entry["body"] += "<h2>First route drill</h2>" + para(
    "Open case 47 by typing its path into a fresh tab. Record the method, status, content type, and first meaningful text returned before scripts run. Disconnect the API and reload. If the page becomes empty, the first response carries too little information. Next submit an inspection note through the native form and record which layer validates it, which layer authorizes the reviewer, and which response confirms storage. This trace establishes the baseline before adding faster client behavior.")
entry["body"] += "<h2>Verification</h2><ul><li>Read the case with scripts disabled and confirm the title and navigation remain.</li><li>Submit a blank note and confirm the server does not create a record.</li><li>Interrupt a valid submission and distinguish an unknown outcome from a confirmed rejection.</li></ul>"
entry["body"] += "<h2>Apply next</h2><p>Build " + link("web-tech/practice-project") + " and check the boundaries in " + link("quizzes/web-development-browser-contracts") + ".</p>"
entry["updated_at"] = stamp

entry = by_path["web-tech/core-concepts"]
entry["body"] += "<h2>Ownership exercise</h2>" + para(
    "Take a case-note form with a theme preference, a signed-in reviewer, and a saved inspection. Write down which layer may change each value. The browser may hold unfinished input and presentation preference; the server decides identity, permission, validation, and commit; the database preserves the accepted record. Now replace the browser script with a direct HTTP client. Every rule that still protects the record belongs on the server or in a database constraint, not in a hidden button or client-side condition.")
entry["body"] += "<h2>Verification</h2><ul><li>Change the case ID in a direct request and test the permission decision.</li><li>Clear browser storage and confirm the saved record still exists.</li><li>Expire the session and verify protected reads and writes fail independently of the visible UI.</li></ul>"
entry["body"] += "<h2>Apply next</h2><p>Use " + link("web-tech/record-level-authorization") + " for the permission boundary and " + link("web-tech/relational-record-modeling") + " for durable relationships.</p>"
entry["updated_at"] = stamp

entry = by_path["web-tech/practice-project"]
entry["body"] += "<h2>Acceptance checks</h2><ul><li>Load the page through a fresh direct URL with scripts disabled; the record title and note form must remain usable.</li><li>Submit a blank note and an unassigned case ID; neither request may create storage state.</li><li>Drop the response after a valid write and document how the user checks whether it committed.</li><li>Run the smoke check against a nested page route after building the release.</li></ul>"
entry["body"] += "<h2>Failure review</h2>" + para(
    "The most revealing trace is a lost response after the database commits. If the browser simply offers Retry, the person may create a second inspection. Record the first request's identity and result so a repeated intent can be recognized, or present an explicit read-back step before another write. Also test a direct path when client routing has never loaded; an in-app click is not proof that the server can serve a copied link.")
entry["body"] += "<h2>Extend the build</h2><p>Move to " + link("web-tech/paginated-inspection-feed-project") + " after the single-case path is correct.</p>"
entry["updated_at"] = stamp

for path, addition, target in [
    ("web-tech/case-intake-end-to-end-project",
     "Add a version field to the stored case and submit two edits from the same base version. Exactly one should commit; the other must return a conflict that preserves the attempted note. Then interrupt the winning response and retry with the same intent key. The retry must identify the committed inspection rather than create a second one. These two tests separate concurrent editing from an uncertain transport result.",
     "web-tech/paginated-inspection-feed-project"),
    ("web-tech/web-release-readiness-project",
     "Include an old-binary compatibility drill in staging before declaring rollback ready. A code rollback cannot repair a schema change that already removed a column the old binary needs. Restore a backup into isolation as a separate drill, compare selected records and media, and record the actual data age and recovery time. A green build alone proves neither direct-route behavior nor recoverability.",
     "web-tech/release-recovery-drill-project"),
]:
    entry = by_path[path]
    entry["body"] += "<h2>Harder boundary</h2>" + para(addition)
    entry["body"] += "<h2>Extend the build</h2><p>Continue with " + link(target) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"deepened_foundation_lessons": len(foundation), "deepened_starting_articles": 2,
                  "deepened_existing_projects": 3}))

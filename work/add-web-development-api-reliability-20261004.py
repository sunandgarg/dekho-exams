"""Add original API mutation and failure contracts."""

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


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


def para(value):
    return f"<p>{html.escape(value)}</p>"


hub = dict(path="web-tech/api-mutation-and-failure-contracts", title="API Mutation and Failure Contracts",
           summary="Prevent lost writes, bound retries, expose long-running work, and make errors usable by clients.",
           overview="An API mutation is a conversation about state, time, and uncertainty. A request can arrive with an old version, time out after a successful commit, be accepted for later processing, or fail with a condition the client can repair. These outcomes need distinct contracts. The case-inspection workflow supplies one running scenario: two reviewers edit a case, a downstream service slows, and a report job runs after the initial request ends. The lessons focus on observable behavior and retry safety across those boundaries.",
           bridges=["web-tech/http-request-response-contract", "web-tech/idempotent-write-requests", "web-tech/background-jobs-and-outbox"])

topics = [
    dict(path="web-tech/conditional-writes-and-lost-update-prevention", title="Conditional Writes and Lost-Update Prevention",
         summary="Require a current representation version before applying a case mutation.",
         definition="A lost update occurs when two clients read the same resource and a later save silently overwrites the first client's change. A conditional write makes the client's observed version part of the request. The server emits a strong representation validator, and the client sends that validator in If-Match when changing the case. If the validator no longer matches, the server rejects the write before applying it. A missing required precondition can receive a distinct response from a failed precondition. This only works when every relevant representation change advances the validator and the comparison happens atomically with the write, not in a separate read followed by an unchecked update.",
         case="Reviewers 29 and 31 both open case 47 at version 62. Reviewer 29 adds a safety note and saves version 63. Reviewer 31 still has version 62 and changes the status to resolved. Without a precondition, the second save can replace the note or overwrite a decision made from stale context. The server rejects reviewer 31's old validator. The interface fetches the current case, shows the difference, and asks for an informed merge or new action. It must preserve reviewer 31's unsaved text while doing so.",
         code='function conditionalCaseUpdate(ifMatch, currentVersion) {\n  if (ifMatch === null) return { status: 428, nextVersion: currentVersion };\n  const expectedTag = `"case-47-v${currentVersion}"`;\n  if (ifMatch !== expectedTag) return { status: 412, nextVersion: currentVersion };\n  return { status: 200, nextVersion: currentVersion + 1 };\n}\nconsole.log(conditionalCaseUpdate(`"case-47-v62"`, 63).status);\n// Output: 412', language="javascript",
         implementation="The function illustrates response decisions, not a transaction. In production, compare the current version and apply the mutation in one atomic database operation, then return the new strong validator with the representation. If a case has multiple variants, be precise about which selected representation the validator covers. A weak validator is not suitable for a lost-update guard. Authorization and field validation still run; a matching validator does not grant permission or make the submitted data valid. For a failed condition, return enough safe current-state information for recovery without leaking another user's private fields.",
         cost="A version check is O(1) for one record, and an atomic conditional update can use the record key and version in a single indexed write. The greater cost is the conflict workflow: users may need to review differences and reapply a change. A validator stored per resource adds little data, but every relevant mutation must advance it consistently. High-write records can see frequent conflicts. Do not hide that by retrying a conflicting write automatically; an automatic retry can reintroduce the overwrite the precondition was meant to prevent.",
         failure="A handler reads version 62, checks If-Match, and then writes without including the version in the database update predicate. Another request commits version 63 between the check and write, so both saves succeed. The API reports a new validator even though one edit was lost. Reproduce with two concurrent requests and move the comparison into the atomic write. Separately test an omitted header and a stale one, since they are different client errors. Preserve the rejected user's draft during recovery.",
         drill="Open case 47 in two sessions at version 62. Save a note in one and a status change in the other. The second request must not silently win. Inspect the HTTP status, returned validator, and stored record after both orders. Remove If-Match and check the required-precondition response. Then deliberately race the server between validation and persistence; if both writes succeed, the database condition is missing. Repeat with a user who lacks permission to ensure the validator is not treated as authority.",
         decision="Use a strong conditional validator for collaborative writes and enforce it in the same atomic operation that changes the resource.",
         checks=["Two concurrent edits from one version cannot both overwrite the same record silently.", "Missing and stale preconditions produce distinct recoverable responses.", "Conflict recovery preserves the user's draft and rechecks authorization."],
         mistakes=["Checking a version in one query and writing without the version predicate.", "Using a weak validator as a lost-update guard.", "Automatically retrying a rejected conflict with the newest version."],
         related=["web-tech/cache-etag-revalidation", "web-tech/transactions-and-concurrent-writes", "web-tech/idempotent-write-requests"]),
    dict(path="web-tech/request-deadlines-retries-and-backoff", title="Request Deadlines, Retries, and Backoff",
         summary="Spend one bounded time budget and retry only operations whose effects are safe to repeat.",
         definition="A timeout means the caller stopped waiting; it does not prove the server did not commit the operation. Retrying blindly can duplicate work and amplify an outage. Give a request an end-to-end deadline, allow only a small number of attempts inside it, and retry only errors that are transient and safe for that operation. A GET is generally easier to retry than a mutation with unknown commit outcome; a mutation needs an idempotency contract or a status lookup. Backoff with jitter reduces synchronized repeat traffic. Honor an explicit server retry delay when applicable, while still respecting the caller's own deadline.",
         case="The case service sends an update to an image-analysis dependency. The connection drops after the dependency accepts the job, and the local handler cannot tell whether it started. A client that retries immediately may create duplicate analysis work. Give the operation a stable idempotency key and query its status where supported. If a transient 503 occurs before acceptance, wait within a bounded retry budget using varied delays. The reviewer should see whether the action is still pending, definitively failed, or safe to retry; a generic spinner after the deadline is not a contract.",
         code='function mayRetryRequest({ status, attempt, remainingMs, repeatSafe }) {\n  if (!repeatSafe || attempt >= 3 || remainingMs < 250) return false;\n  return status === 429 || status === 502 || status === 503 || status === 504;\n}\nconsole.log(mayRetryRequest({ status: 503, attempt: 2, remainingMs: 900, repeatSafe: true }));\n// Output: true', language="javascript",
         implementation="This predicate decides eligibility, not the delay. A production caller should attach an absolute deadline to all attempts, cap each connection and response wait, and compute bounded backoff with jitter. A server-provided retry delay is advice, not permission to exceed the user's remaining time. Decide which HTTP outcomes are retryable for the specific operation; 429 and 503 may be candidates, whereas a validation error or stale If-Match condition requires user or client correction. Do not stack independent retry loops in browser, API gateway, and downstream client without a total attempt budget.",
         cost="One attempt costs one request; three attempts can triple work during a partial outage. Backoff lowers synchronized pressure but increases latency for the affected user. A deadline bounds that exposure and makes failure visible, while a too-short deadline can abandon work that would have completed. Measure success after retry, extra attempt count, dependency saturation, and end-to-end latency. An idempotency record or operation status endpoint adds storage and cleanup cost but is often cheaper than duplicate side effects.",
         failure="A client retries every 500 response three times, while the gateway and downstream SDK also retry. One user action fans out into many calls just as the dependency is failing. Another client retries a timed-out POST without a stable key, creating two analysis jobs. Define one retry owner, cap total attempts and time, and make the mutation repeat-safe before automatic retry. Test a timeout after commit, an immediate 503, a rate limit with retry advice, and a deadline that expires during backoff.",
         drill="Instrument one case-analysis request with an idempotency key and a five-second overall deadline. Force a 503 before acceptance, a dropped response after acceptance, and a validation error. Record attempted calls, wait time, final user state, and downstream job count. Add jitter to concurrent callers and compare traffic bursts. Then enable a second retry layer on purpose to see amplification, remove it, and document the single owner of the retry budget.",
         decision="Retry only when the operation is safe to repeat, the failure is plausibly transient, and the caller still has time budget.",
         checks=["A timeout after commit does not create a duplicate job on retry.", "Transient retries stop at the attempt and overall-deadline limits.", "Validation and stale-version failures are not retried as transient errors."],
         mistakes=["Equating timeout with proof that no side effect occurred.", "Allowing every network layer to run its own retry loop.", "Ignoring a remaining deadline while waiting through backoff."],
         related=["web-tech/idempotent-write-requests", "web-tech/rate-limits-and-request-budgets", "web-tech/observability-and-recovery"]),
    dict(path="web-tech/accepted-operations-and-status-resources", title="Accepted Operations and Status Resources",
         summary="Represent work that continues after the request as a durable operation with a readable outcome.",
         definition="An accepted response means the server has taken responsibility for later processing; it does not mean the task succeeded. For a long-running case report, first persist an operation record and a job request durably, then return an accepted response with a status resource the client can read. The status representation should distinguish queued, running, succeeded, failed, and cancelled states, with stable identifiers and safe error information. Define whether cancellation is best effort and what happens if it arrives after completion. Expire completed status records under a published lifetime, and keep final report access subject to normal authorization.",
         case="Reviewer 29 requests a report for 62 cases. The report takes longer than an ordinary HTTP response, so the API creates operation 847, records its owner, queues the job, and responds with a path to the operation state. The browser can leave and return without losing the job. If the worker fails after generating 47 cases, the status must say failed or partial according to the product contract; it cannot keep showing running forever. Another reviewer must not learn about the report merely by guessing operation 847's identifier.",
         code='function acceptedReport(operationId) {\n  return {\n    status: 202,\n    headers: { Location: `/api/report-operations/${operationId}` },\n    body: { operationId, state: "queued" }\n  };\n}\nconsole.log(acceptedReport(847).body.state);\n// Output: queued', language="javascript",
         implementation="Return this response only after the operation and enqueue intent are committed. An in-memory task started after responding can vanish on process restart. The status endpoint checks the caller's authority and returns a machine-readable state, progress only when it is accurate, and a final result link only for an authorized user. Polling should have a reasonable interval and backoff; a live channel can reduce delay but needs reconnect rules. The client should stop polling after a terminal state or a user-visible timeout without assuming the server cancelled the work.",
         cost="Durable operation records, worker capacity, and status polling add storage and request traffic. For n reports polled every p seconds, status requests scale roughly with n/p while they remain active, so set a sensible interval and terminal cleanup. Holding an HTTP connection open for a short task may be simpler; use a status resource when work duration or disconnect recovery justifies it. Progress estimates can be expensive or misleading, so a coarse stage label may be more honest than an invented percentage.",
         failure="The API returns 202 before writing the operation record. A process restarts between response and enqueue, leaving a client with a status path that returns not found forever. Commit first, then respond. Another failure is a worker that marks the report succeeded before the output file is durable; the client follows the result link and gets an error. Test crash points around acceptance and completion, and verify status transitions, authorization, expiry, and idempotent repeat requests under one operation key.",
         drill="Start a report, capture the operation path, close the browser, and return from a second session of the same user. Verify queued, running, and terminal states. Kill the API process immediately after acceptance and verify the worker still finds the job. Fail the worker after partial output and inspect the final state. Try the status path as another user, then repeat the original request with the same idempotency key and confirm it maps to the intended operation rather than creating a duplicate.",
         decision="Use a durable status resource when work outlives a normal request, and make acceptance, ownership, and terminal outcome observable.",
         checks=["A restart immediately after 202 does not lose the operation.", "Status transitions and terminal result access are authorized and accurate.", "Repeated submission with one idempotency key does not create two reports."],
         mistakes=["Returning 202 before persisting the operation and enqueue intent.", "Using a status identifier as the only access control.", "Reporting success before the final result is durable."],
         related=["web-tech/background-jobs-and-outbox", "web-tech/idempotent-write-requests", "web-tech/record-level-authorization"]),
    dict(path="web-tech/structured-api-errors-and-recovery", title="Structured API Errors and Recovery",
         summary="Give clients stable error classes without exposing private internals or confusing status codes.",
         definition="An API error response needs two audiences: software that must choose a recovery path and a person who must understand what happened. Use an appropriate HTTP status, a stable machine-readable problem type or code, a concise title, and safe detail when it helps the task. A request identifier can connect the response to operational logs without copying a private case body into the error. Field validation may include paths or field names, but never trust the client to interpret a human sentence as the only programmatic signal. Keep permission and existence decisions deliberate so errors do not disclose hidden records.",
         case="Reviewer 31 tries to resolve case 47 with an old version. The API should return a failed-precondition status and a stable error code the UI recognizes as a merge conflict. The UI then offers to compare current data while preserving the unsaved note. A malformed note should instead mark the field to correct. A temporarily unavailable report worker should offer a later retry or status check. If all three failures are returned as status 200 with {success:false}, caches, monitoring, and generic clients lose the distinction.",
         code='function versionConflictProblem(requestId) {\n  return {\n    status: 412, type: "about:blank", title: "Precondition failed",\n    detail: "This case changed before your save.", code: "case_version_conflict", requestId\n  };\n}\nconsole.log(versionConflictProblem("req-47").code);\n// Output: case_version_conflict', language="javascript",
         implementation="Send the representation with an error media type if the API adopts the problem-details format, and keep its status member consistent with the actual HTTP status. The generic type in this sketch is enough because the stable extension code drives the application's recovery decision; a product may use its own type identifier instead. Do not put stack traces, SQL, tokens, or another user's private note in detail. Use field identifiers the UI can map to controls, and allow the human message to be localized without changing the machine code. A 404 or 403 policy for hidden records must be consistent across routes.",
         cost="A common error shape adds a little response data and shared handling code, but reduces endpoint-specific parsing and ambiguous recovery. Versioning the machine code requires care: removing or reusing a code can break older clients. Keep a small registry of codes, statuses, and intended client actions. Logging only request IDs and classified errors keeps the response safe, but support teams need a controlled path from that ID to diagnostics. Avoid recording unbounded raw validation input as an error extension.",
         failure="A handler catches every exception and returns 200 with a free-text message. The case UI treats a failed save as success because it only checks response.ok; the reviewer leaves and loses the note. Another handler returns a detailed database error to help support, exposing internal table names and a private value. Test status and body together for conflict, validation, denial, and dependency failure. Make the UI branch on stable code and preserve its draft until the mutation is confirmed, not until any response arrives.",
         drill="Send four bad requests: stale version, missing required note, forbidden case, and temporarily unavailable worker. Write the expected status, machine code, safe detail, and UI recovery for each before implementing handlers. Inspect actual responses for tokens, raw note text, stack traces, and internal paths. Change the human wording and confirm the client still behaves correctly. Then simulate an old client that does not know a new code; it should fall back to a safe generic error rather than report success.",
         decision="Use status codes for transport meaning and stable machine codes for product recovery, while keeping human detail safe and replaceable.",
         checks=["Conflict, validation, denial, and dependency failures have distinct status/code pairs.", "Changing human wording does not change the client's recovery branch.", "Error bodies contain no raw private content, credentials, or internal stack traces."],
         mistakes=["Returning status 200 for a failed mutation.", "Branching on a localized human sentence as the sole error code.", "Exposing internal exceptions to make debugging easier."],
         related=["web-tech/route-parameters-and-error-responses", "web-tech/api-evolution-and-compatibility", "web-tech/telemetry-minimization-and-retention"]),
]

assert len(topics) == 4


def add_entry(path, title, summary, entry_type, section_path, sort_order):
    assert path not in by_path, path
    template = "web-tech/getting-started" if entry_type == "article" else "web-tech/web-technology"
    entry = copy.deepcopy(by_path[template])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), type=entry_type,
                 path=path, title=title, summary=summary, category="Web Development",
                 subject="web-tech", difficulty="Intermediate" if entry_type == "article" else None,
                 tags=["web-tech", "web-development"], sort_order=2200 + sort_order,
                 status="published", created_at=stamp, updated_at=stamp, published_at=stamp, body="")
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": section_path,
                     "content_format": "html", "seo_ready": False}
    if entry_type == "article":
        entry["data"].update(kind="tutorial", author_path="authors/aitrove-editorial", reading_minutes=8)
    entries.append(entry)
    by_path[path] = entry
    return entry


add_entry(hub["path"], hub["title"], hub["summary"], "subject", hub["path"], 0)
for number, topic in enumerate(topics):
    add_entry(topic["path"], topic["title"], topic["summary"], "article", hub["path"], 10 + number)

for topic in topics:
    entry = by_path[topic["path"]]
    subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"],
                   text=True, capture_output=True, check=True)
    siblings = [item["path"] for item in topics if item["path"] != topic["path"]]
    related = [hub["path"]] + siblings + topic["related"]
    body = para(topic["definition"])
    body += "<h2>Working case</h2>" + para(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>"
    body += para(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + para(topic["cost"])
    body += "<h2>Failure trace</h2>" + para(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join(f"<li>{html.escape(check)}</li>" for check in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + para(topic["drill"])
    body += "<h2>Decision note</h2>" + para(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in topic["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><p>" + "; ".join(link(path) for path in related) + ".</p>"
    entry["body"] = body
    entry["data"].update(related=related, reading_minutes=max(6, round(len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", body))) / 155)))

hub_entry = by_path[hub["path"]]
hub_entry["data"]["modules"] = [{"title": hub["title"], "summary": hub["summary"], "lessons": [topic["path"] for topic in topics]}]
hub_entry["data"]["resource_tabs"] = [{"title": "Web Development", "path": "web-tech/web-technology"},
                                      {"title": "Projects", "path": "web-tech/web-technology/project"},
                                      {"title": "Quizzes", "path": "web-tech/quizzes"}]
hub_entry["body"] = para(hub["overview"])
hub_entry["body"] += "<h2>Topics in this track</h2><ul>" + "".join(f'<li>{link(topic["path"])} — {html.escape(topic["summary"])}</li>' for topic in topics) + "</ul>"
hub_entry["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in hub["bridges"]) + ".</p>"

root_entry = by_path["web-tech/web-technology"]
root_entry["data"]["modules"].append({"title": hub["title"], "summary": hub["summary"],
                                      "lessons": [hub["path"]] + [topic["path"] for topic in topics]})
root_entry["body"] += f'<h2>{link(hub["path"])}</h2><p>{html.escape(hub["summary"])}</p><ul>' + "".join(
    f'<li>{link(topic["path"])} — {html.escape(topic["summary"])}</li>' for topic in topics) + "</ul>"
root_entry["updated_at"] = stamp

for path, targets in {
    "web-tech/backend-api-systems": [hub["path"]],
    "web-tech/cache-etag-revalidation": [topics[0]["path"]],
    "web-tech/idempotent-write-requests": [topics[0]["path"], topics[1]["path"]],
    "web-tech/background-jobs-and-outbox": [topics[2]["path"]],
    "web-tech/api-evolution-and-compatibility": [topics[3]["path"]],
}.items():
    entry = by_path[path]
    entry["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": len(topics)}))

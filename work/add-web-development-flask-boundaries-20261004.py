"""Add original advanced Flask web-development lessons and connect the curriculum."""
import ast
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


def paragraph(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/flask-context-and-service-boundaries"
hub_title = "Flask Context and Service Boundaries"
topics = [
    dict(
        slug="flask-request-context-and-object-authorization",
        title="Flask Request Context and Object Authorization",
        summary="Extract a caller identity during the request, then check the exact permit before returning fields.",
        concept="Flask supplies request, session, current_app, and g through context-local proxies. Their convenient syntax can hide their lifetime: the active request owns them, and an application context does not make a request object available to a worker. A service that reads request or g deep inside its logic becomes difficult to test and impossible to run unchanged from a queue consumer. Authenticate at the HTTP edge, turn the caller into an explicit immutable identity, and pass that identity to a service. Permission must then be checked for the requested case, action, and current assignment. A matching route integer is merely a lookup. A valid login is not permission for every permit in the database.",
        case="Reviewer 47 opens case 62; reviewer 81 guesses the same path. Both have valid sessions. A handler that queries PermitCase by ID and returns the ORM object's dictionary reveals the district's private note to reviewer 81. The navigation menu filters unauthorized cases, but that only changes the menu. A later export endpoint repeats the same ID lookup and leaks the note even after the detail page is repaired. The corrected service queries the case and its reviewer assignment together, returns a narrow response projection, and uses the same authorization rule for export metadata. An approval command checks again because assignments can change between the GET and POST requests.",
        implementation="Keep a private blueprint behind authentication middleware or a before-request guard. Derive reviewer_id from the validated server session, not a request parameter. Pass that scalar into a query that scopes PermitCase to authorized reviewer assignments. For a hidden private case, choose one deliberate missing-style response for both nonexistent and forbidden IDs; internal logs may retain a safe request ID and reason. Project only fields the caller may receive, even after the scope check. Code outside Flask request handling should accept reviewer_id and case_id as parameters. Do not pass LocalProxy objects into a thread or queue; resolve the needed data while the request is active, then use a separate worker context and fresh database session.",
        cost="A permission-scoped detail query is usually an indexed case lookup plus an indexed assignment predicate. It may cost another join or existence check compared with an unsafe primary-key lookup, but it avoids fetching fields that must later be discarded. For a list, put the reviewer predicate in SQL rather than querying every case and filtering Python objects; otherwise memory, query count, and disclosure risk grow with the whole table. Repeated policy checks across 47 rows can create an N+1 pattern if each check loads a relationship. Measure SQL count, returned row count, and serialization width on allowed, denied, and missing paths. The public response should be small even if the database model is wide.",
        failure="Exercise the same route anonymously, as reviewer 47, as reviewer 81, and with an ID that has never existed. Compare forbidden and absent responses against the chosen disclosure policy. Try the export endpoint and any document-download path with the guessed case ID. Revoke reviewer 47's assignment after loading the page, then submit approval; the write service must reject stale access. Give the model a private_note value that would be obvious in a leaked response and assert it is absent from JSON. Run the service in a plain unit test with explicit reviewer_id; if it reads request or g, the boundary has been breached.",
        drill="Build a Flask blueprint for private permit detail and export metadata. Seed cases 62 and 81 with disjoint reviewers. Give one case a private district note and an attachment path. Authenticate the caller once at the HTTP edge, then pass its integer identity into a query service. Make the service return a response record containing only case ID, public title, and status. Test unknown, forbidden, allowed, and revoked cases. Reuse the same scoped lookup for export authorization. Log an opaque request ID for a denial without printing the hidden case title. Count queries for a 47-case reviewer list before and after moving the permission predicate into SQL.",
        decision="Treat Flask context as an HTTP convenience; make authorization and data projection explicit service inputs and outputs.",
        code='''from flask import Blueprint, abort, jsonify, session
from sqlalchemy import select
from .database import db
from .models import PermitCase, PermitReviewer

permits = Blueprint("permits", __name__)

@permits.get("/permits/<int:case_id>")
def permit_detail(case_id: int):
    reviewer_id = session.get("reviewer_id")
    if reviewer_id is None:
        abort(401)
    statement = (
        select(PermitCase.id, PermitCase.title, PermitCase.status)
        .join(PermitReviewer, PermitReviewer.case_id == PermitCase.id)
        .where(PermitCase.id == case_id, PermitReviewer.reviewer_id == reviewer_id)
    )
    case = db.session.execute(statement).one_or_none()
    if case is None:
        abort(404)
    return jsonify({"case_id": case.id, "title": case.title, "status": case.status})''',
        checks=["A signed-in reviewer still needs permission for the exact case.", "Response fields are projected rather than serialized from the model.", "The service can run without a Flask request proxy."],
        mistakes=["Treating a filtered menu as an authorization rule.", "Passing request or g into a background thread.", "Checking permission for detail but forgetting export and mutation routes."],
        related=["python/flask-routing", "python/flask-json-api", "web-tech/authorization-and-tenant-boundaries"],
    ),
    dict(
        slug="flask-sqlalchemy-session-and-query-lifetime",
        title="Flask-SQLAlchemy Session and Query Lifetime",
        summary="Bound queue reads, avoid relation N+1 work, and return plain values before the app context ends.",
        concept="Flask-SQLAlchemy's session belongs to the active application context and is removed when that context ends. A view may use it safely during request handling; an ORM object handed to a background thread, response generator, or later callback is a poor transfer format. Lazy attributes can trigger database access after the session is gone, or keep a connection occupied for an unexpectedly long response. The query should express both the caller's scope and the exact fields the page needs. A list of 47 permit cards needs IDs, titles, district labels, and counts. It does not need every attachment object, internal note, or a cursor that silently drops ties in creation time.",
        case="A permit queue initially retrieves 47 cases and then reads case.district.name in a template. Each relationship access issues another query. A rushed fix eagerly loads all attachments too, causing one permit with thousands of scans to inflate memory. Another developer returns ORM cases inside a streaming CSV generator; the view has already returned when the generator runs, so lazy reads may fail or hold a session across a slow client. The corrected list applies reviewer scope in SQL, selects the displayed scalar columns, computes attachment counts in the database, orders by created_at and ID, and materializes the bounded response while the request context exists.",
        implementation="Use a select statement with an assignment join or exists predicate. Build a count subquery for attachments rather than loading the collection. For one-to-many relations that really must be shown, selectinload can batch children for a bounded page; for a to-one relation, joinedload can avoid repeated district reads. Prefer a scalar projection when the endpoint only needs a few columns. Cursor continuation must use the same reviewer predicate on every request and a unique tie breaker. A client cursor is not a permission token. For large exports, create a durable export job with an explicit actor and query parameters; let its worker open its own application context and session, then store an artifact for download.",
        cost="A 47-row scalar page has O(47) response memory, while a full eager load costs O(parents plus children), which may be unbounded in practice. An attachment count subquery uses indexed database work and avoids transferring all attachment rows, but it still needs a plan check under large attachment tables. Cursor paging can avoid the increasing skip cost of deep offsets when the order and scope have usable indexes; it gives up cheap numbered-page navigation and exact totals. A long-running streamed query may tie up a database connection for the duration of the client's download. Observe query count, rows transferred, memory, connection occupancy, and the plan for a deep page, not just wall-clock time on an empty fixture.",
        failure="Seed 47 cases with repeated timestamps and follow continuation through the entire queue without duplicate or missing IDs. Add one case with 620 attachments and verify the list obtains its count without hydrating 620 models. Remove the district join in a negative test and record the per-row query rise. Submit the same cursor as reviewer 81 and confirm the reviewer scope remains on the SQL query. Close the request context before consuming a deliberately lazy generator and confirm that test detects the invalid dependency. Simulate a slow export client; the normal request path should not keep a database transaction or connection open for the download duration.",
        drill="Implement a bounded reviewer queue with 47 items per page. Display case ID, title, district, attachment total, and created time. Use explicit scalar output records. Compare a lazy district relationship, a bounded joined district query, and an unnecessary attachment eager load while recording query and row counts. Add a composite index that matches reviewer scope and sort order where the actual schema permits it. Create timestamp ties and verify deterministic next-page behavior. Move the CSV export to a worker that receives only reviewer identity and filter values, opens a fresh application context, and writes an artifact. Ensure the artifact download performs a new permission check.",
        decision="Finish database work inside a bounded context, then hand plain response data or durable job identifiers to later stages.",
        code='''from sqlalchemy import func, select
from .database import db
from .models import Attachment, District, PermitCase, PermitReviewer

attachment_total = (
    select(func.count(Attachment.id))
    .where(Attachment.case_id == PermitCase.id)
    .correlate(PermitCase)
    .scalar_subquery()
)
statement = (
    select(PermitCase.id, PermitCase.title, District.name, attachment_total)
    .join(PermitReviewer, PermitReviewer.case_id == PermitCase.id)
    .join(District, District.id == PermitCase.district_id)
    .where(PermitReviewer.reviewer_id == reviewer_id)
    .order_by(PermitCase.created_at.desc(), PermitCase.id.desc())
    .limit(47)
)
cards = [tuple(row) for row in db.session.execute(statement).all()]''',
        checks=["Reviewer scope is part of SQL on every page.", "The response holds scalar values instead of detached ORM models.", "An attachment count does not load every attachment object."],
        mistakes=["Using a long-lived request session as a worker session.", "Fixing N+1 by eagerly loading unbounded collections.", "Ordering a cursor only by a nonunique timestamp."],
        related=["python/flask-sqlite-persistence", "python/flask-keyset-list", "web-tech/data-persistence"],
    ),
    dict(
        slug="flask-command-validation-and-transaction-replay",
        title="Flask Command Validation and Transaction Replay",
        summary="Separate HTTP parsing, browser CSRF, case permission, and one committed approval outcome.",
        concept="A Flask route receives an HTTP command, not a trusted model update. JSON parsing can establish that a body is present and syntactically valid; it cannot establish that reviewer 47 may approve case 62. Browser CSRF protection answers another question about credentialed submissions, while a transaction answers whether the case state, audit row, and outbox intent commit together. Those boundaries should stay separate. A dropped response after commit leaves the browser unable to tell whether approval happened. Give the logical command a stable operation ID, store its result under a unique database constraint, and let an exact replay retrieve the original outcome. A changed payload under the same ID must be rejected rather than silently treated as the original command.",
        case="A reviewer clicks Approve while case 62 is in review. The server commits approval and its audit row, but a proxy drops the response. The browser retries with a new operation ID and a second audit event appears. A different reviewer sends well-formed JSON with a guessed case ID; an input validator accepts it, yet the reviewer has no assignment. The repaired route checks content type and body limits, validates the operation ID and expected revision, derives identity from a server session, and delegates to a transaction service. That service checks current assignment and case state under a lock, inserts one operation and outbox row, commits, and returns the stored result for a byte-equivalent replay.",
        implementation="Set an application-wide request-body limit suitable for this endpoint family and reject non-JSON content before parsing. Validate a strict object shape and bounded values; a Python bool must not slip through an integer revision check, since bool subclasses int. Protect cookie-authenticated browser mutations with a real CSRF mechanism; SameSite cookies alone do not settle every threat model. In the service, compare the command's expected revision against locked current state, and use a uniqueness constraint on reviewer and operation ID or another deliberate namespace. Store a digest of the canonical command fields with the outcome. Make the transaction own case change, operation record, and outbox row. Never send email inside a database transaction that might be retried.",
        cost="JSON and token checks are cheap compared with contention on a hot case. A row lock serializes conflicting approvals and can increase tail latency, so keep the transaction short and avoid provider calls within it. Operation records occupy storage for the defined replay horizon; deleting them too early permits old retries to repeat the effect. An outbox row adds a write but makes promised delivery observable after a crash. A replay read can return quickly without taking another approval lock once the committed operation is found, provided the stored payload digest matches. Monitor lock waits, duplicate-operation conflicts, stale revision responses, outbox age, and body-size rejection rather than using only successful HTTP counts.",
        failure="Send malformed JSON, an array body, a bool revision, an oversized body, and a valid command from reviewer 81. None may mutate case 62. Submit a browser form without its CSRF token and verify the guard runs before business logic. Race two approval requests with the same operation ID; inspect the database for one case transition, one audit result, and one outbox event. Commit and discard the response, then replay the exact command and require the saved result. Change the reason while reusing the ID and require a conflict. Inject failure before the outbox insert and verify case state and audit roll back together. Revoke assignment between read and write and confirm the transaction checks current authorization.",
        drill="Implement a Flask approval command for permit 62. Specify a stable operation ID, expected revision, and bounded reason. Write an input parser that rejects bool as a revision and refuses unknown keys. In a service, lock the case row where the database supports it, verify reviewer assignment, and store case state, operation result, and outbox event atomically. Add a uniqueness constraint rather than a process-local set. Test exact replay, changed-payload replay, concurrent same-key requests, rollback, stale revision, and revoked assignment. Record the result's public fields separately from internal audit details. Explain how the chosen database handles lock syntax and serialization conflicts.",
        decision="The HTTP edge validates a command; the database arbitrates its one authorized, replayable outcome.",
        code='''import re
from flask import abort, jsonify, request, session
from .security import csrf

def approve_permit(case_id: int, approval_service):
    csrf.protect()
    if not request.is_json:
        abort(415)
    command = request.get_json(silent=True)
    if not isinstance(command, dict):
        abort(400)
    if set(command) != {"operation_id", "expected_revision", "reason"}:
        abort(400)
    revision = command["expected_revision"]
    operation_id = command["operation_id"]
    reason = command["reason"]
    if type(revision) is not int or revision < 0:
        abort(400)
    if not isinstance(operation_id, str) or not re.fullmatch(r"[a-f0-9]{32}", operation_id):
        abort(400)
    if not isinstance(reason, str) or not 1 <= len(reason) <= 500:
        abort(400)
    reviewer_id = session.get("reviewer_id")
    if reviewer_id is None:
        abort(401)
    result = approval_service.approve_once(reviewer_id, case_id, command)
    return jsonify({"case_id": result.case_id, "status": result.status})''',
        checks=["Malformed bodies and bool revisions are rejected before write work.", "Current permission and expected revision are checked inside the transaction.", "An exact replay returns one stored outcome; a changed replay conflicts."],
        mistakes=["Confusing valid JSON with authorization.", "Using an in-memory set to arbitrate concurrent retries.", "Calling an email provider from a transaction closure."],
        related=["python/flask-error-boundaries", "python/flask-if-match-write", "web-tech/api-mutation-and-failure-contracts"],
    ),
    dict(
        slug="flask-async-views-and-durable-background-work",
        title="Flask Async Views and Durable Background Work",
        summary="Use async for awaited I/O inside a request, then persist work that must survive the response.",
        concept="Flask supports async views when the async extra is installed, but its WSGI request still occupies one worker for the request-response cycle. Awaiting independent I/O can shorten one response; adding async def does not raise the number of simultaneous requests that the existing worker pool can serve. A task created inside an async view is not a durable background job. Once the view completes, its event loop may stop and unfinished child tasks are cancelled. For a promised permit notification or export, record intent transactionally and let a separate worker process it. This is also a context boundary: a worker cannot reuse request, g, or a Flask-SQLAlchemy session from the original view.",
        case="After approving permit 62, a route calls asyncio.create_task to send a notice and immediately returns 200. In tests with a fast fake sender, the notice appears. Under a slower provider, the view finishes and the task is cancelled; case 62 remains approved but no notice is sent. Replacing the function with async def does not repair the delivery contract. The corrected approval transaction stores outbox event 93 with the state change. A queue notification may wake a worker, but a periodic sweep also finds unsent events if that wake-up is lost. The worker opens its own app context, claims event 93 under a lease, sends with a stable event key, and records delivery state.",
        implementation="Use async views only when the awaited dependencies are actually asynchronous and their concurrency benefits one request. Check extension decorators for async compatibility. Keep synchronous database calls out of an event loop unless an appropriate bridge or worker thread owns them; merely writing await around sync code does nothing. For durable effects, insert an outbox row in the approval transaction. After commit, enqueue its ID as a wake-up hint, then sweep pending IDs independently. Worker input should be immutable identifiers and serialized command data, never request proxies or ORM instances. Open a fresh app context for Flask-SQLAlchemy access, claim with a lease, and acknowledge after a provider result. A timeout may mean accepted-but-unacknowledged delivery, so reconcile or retry under the same event identity.",
        cost="An async view consumes a WSGI worker while it runs, although concurrent awaited I/O may reduce its latency. The outbox adds a database write and storage per committed event; sweep scans and lease updates consume database capacity, and a worker pool needs its own operational budget. Sending large payloads or blocking libraries from the event loop reduces the benefit of async. At-least-once processing can duplicate an external effect when acknowledgment is lost, so a provider idempotency key or reconciliation endpoint matters. Track oldest pending age, claim lease expiry, attempt count, provider response class, request worker occupancy, and queue lag. A 200 response proves the approval commit, not final delivery.",
        failure="Use a slow fake sender to show that a spawned task is cancelled after an async view returns; do not treat a fast local pass as proof of background execution. Roll back an approval and verify no outbox event exists. Commit the case and kill the process before queue submission; restart the sweep and confirm it finds event 93. Crash a worker after claim, let its lease expire, then reclaim the same ID. Timeout after the provider may have accepted a send and ensure retries use that same identity. Stop all workers and confirm monitoring shows pending age rising. Run a worker with no request context and verify it succeeds using its own app context and fresh session.",
        drill="Build notification delivery for a permit approval. In the approval transaction, persist the case change and event 93. Enqueue event 93 only as a hint after commit. Give the worker a bounded lease, attempt budget, and durable delivered or review-needed state. Add a scheduled sweep that scans 47 pending events per pass. Test rollback, post-commit process failure, worker restart, lost provider acknowledgment, and an invalid permanent recipient. Separately write an async view that awaits two independent noncritical lookups, measure its latency and WSGI worker occupancy, and compare it with the synchronous version. Document which behavior is request latency optimization and which behavior is durable delivery.",
        decision="Await only request-scoped I/O; use a committed outbox and independent worker for promised effects.",
        code='''from flask import current_app

def deliver_outbox_event(app_factory, event_id: int) -> None:
    application = app_factory()
    with application.app_context():
        outbox = current_app.extensions["permit_outbox"]
        claimed = outbox.claim_with_lease(event_id)
        if claimed is None:
            return
        try:
            receipt = outbox.sender.send(claimed.payload, key=claimed.event_key)
        except TimeoutError:
            outbox.mark_retryable(event_id)
            return
        outbox.mark_delivered(event_id, receipt)''',
        checks=["The worker receives an event ID and opens its own app context.", "A database row survives a lost queue wake-up.", "An ambiguous provider result retains the same event identity."],
        mistakes=["Calling asyncio.create_task and returning before promised work completes.", "Assuming async def increases WSGI worker concurrency.", "Passing request proxies or live ORM models to a worker."],
        related=["python/flask-conditional-response", "web-tech/background-workflow-reliability", "web-tech/fastapi-lifespan-background-work-and-delivery-state"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/fastapi-contract-and-resource-boundaries"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Build Flask permit services with explicit request context, bounded SQL, replay-safe writes, and durable background work.",
           sort_order=3740, created_at=stamp, updated_at=stamp, published_at=stamp)
hub["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path, "content_format": "html",
               "seo_ready": False, "modules": [], "resource_tabs": [
                   {"title": "Web Development", "path": "web-tech/web-technology"},
                   {"title": "Projects", "path": "web-tech/web-technology/project"},
                   {"title": "Quizzes", "path": "web-tech/quizzes"}]}
entries.append(hub)
by_path[hub_path] = hub

for number, topic in enumerate(topics):
    path = "web-tech/" + topic["slug"]
    assert path not in by_path
    ast.parse(topic["code"])
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3741 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-python">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + paragraph(topic["cost"]) + "<h2>Failure trace</h2>" + paragraph(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + paragraph(topic["drill"]) + "<h2>Decision note</h2>" + paragraph(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
    entry["body"] = body
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": hub_path,
                     "content_format": "html", "seo_ready": False, "kind": "tutorial",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": related}
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path["web-tech/" + topic["slug"]]
    entry["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in entry["data"]["related"]) + ".</p>"
hub["data"]["modules"] = [{"title": hub_title, "summary": hub["summary"],
                           "lessons": ["web-tech/" + topic["slug"] for topic in topics]}]
hub["body"] = paragraph("A Flask permit service must keep browser request state, SQL session work, accepted commands, and background effects inside their own lifetimes. Follow reviewer 47 and case 62 through four boundaries: exact permission, bounded queue reads, replayable approval, and durable notification delivery. Each lesson includes a measured cost, a failure trace, and a drill that can expose an unsafe shortcut.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Earlier Flask lessons</h2><p>" + "; ".join(link(path) for path in ["python/flask-routing", "python/flask-json-api", "python/flask-sqlite-persistence", "python/flask-error-boundaries", "python/flask-multipart-budgets", "python/flask-conditional-response", "python/flask-keyset-list", "python/flask-if-match-write"]) + ".</p>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/backend-api-systems", "web-tech/authorization-and-tenant-boundaries", "web-tech/data-persistence"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"],
                                       "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/backend-api-systems": [hub_path],
    "web-tech/authorization-and-tenant-boundaries": ["web-tech/flask-request-context-and-object-authorization"],
    "web-tech/data-persistence": ["web-tech/flask-sqlalchemy-session-and-query-lifetime"],
    "web-tech/api-mutation-and-failure-contracts": ["web-tech/flask-command-validation-and-transaction-replay"],
    "web-tech/background-workflow-reliability": ["web-tech/flask-async-views-and-durable-background-work"],
    "web-tech/fastapi-contract-and-resource-boundaries": [hub_path],
    "python/flask-routing": [hub_path],
    "python/flask-json-api": ["web-tech/flask-request-context-and-object-authorization"],
    "python/flask-sqlite-persistence": ["web-tech/flask-sqlalchemy-session-and-query-lifetime"],
    "python/flask-keyset-list": ["web-tech/flask-sqlalchemy-session-and-query-lifetime"],
    "python/flask-if-match-write": ["web-tech/flask-command-validation-and-transaction-replay"],
}
for path, targets in crosslinks.items():
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4,
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))

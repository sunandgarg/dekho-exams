"""Add original Django request and persistence lessons to the Web Development fixture."""
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


hub_path = "web-tech/django-request-and-persistence-boundaries"
hub_title = "Django Request and Persistence Boundaries"
topics = [
    dict(
        slug="django-middleware-session-and-object-permissions",
        title="Django Middleware, Sessions, and Object Permissions",
        summary="Separate request-wide identity setup from the permission decision for one database row.",
        concept="Django constructs a request through an ordered middleware chain. On the way in, each layer receives a request before the inner view; on the way out, response work unwinds in the other direction. A middleware may also return a response early. This makes registration order part of the behavior, not a cosmetic settings choice. Session middleware must make session state available before authentication middleware resolves the user. Authentication answers who is making the request. It does not answer whether that user may inspect case 62. That second decision belongs at the object boundary and should use a server-owned rule, not a case ID supplied by the browser.",
        case="A municipal permit screen signs in reviewer 47 and shows a link to case 62. Reviewer 81 changes the URL to the same case number and receives the page because the view checks only is_authenticated. A separate logging layer records an anonymous identity because it was placed before authentication and expected request.user to be ready. Fixing the order makes request identity available, but it still does not fix the case leak. The view now queries only rows allowed for the authenticated reviewer and treats any other case as absent. A shared service applies the same scope to exports and background actions.",
        implementation="Keep SessionMiddleware before AuthenticationMiddleware in settings and inspect the whole request chain when adding custom layers. Use the login requirement to reject anonymous access, then filter the requested record by both primary key and reviewer permission. Resolve only fields the response needs. In this case, allowed_reviewers is a many-to-many relation on PermitCase and its permission mapping is maintained by the server. Return 404 for both a nonexistent and an inaccessible private case if revealing existence would be harmful. A write service must repeat the permission predicate inside its own transaction; a view-only check can become stale or be bypassed by another entry point. Log a request identifier separately from private case details.",
        cost="A session lookup and permission query make a private route more expensive than a static page. The filtered lookup can be efficient when the case key and reviewer mapping have suitable indexes; inspect the generated query and actual database plan before assuming that. Fetching a model and following unrelated relations adds hidden queries, so project a small response where practical. A global middleware that queries the database for every path also taxes public pages and health checks. Keep broad identity setup in middleware and expensive object checks close to the resource. Count queries for allowed, denied, anonymous, and missing cases rather than timing only the happy path.",
        failure="Exercise four callers: anonymous, reviewer 47 for assigned case 62, reviewer 81 for case 62, and reviewer 47 for a missing case. The latter two should obey the same disclosure rule. Remove SessionMiddleware in a test configuration and observe that authentication no longer has its prerequisite; restore the order. Then introduce a second route for an export and confirm that it reuses the object permission boundary rather than trusting a prior screen visit. Reassign the case between a read and an attempted write. The write must still check the current mapping before committing. Record the query count for the denied path.",
        drill="Create two reviewers and three permit cases, with one case shared only where policy allows. Write a private JSON detail route and a separate export route. First demonstrate the wrong behavior when login is treated as case permission. Then bind both routes to a common server-side scope and add tests for guessed IDs. Check settings order for session and authentication middleware. Inspect logs to ensure rejected URLs do not leak titles or submitted tokens. Finally, remove a reviewer's assignment just before a command and verify the command service rejects it under current database state.",
        decision="Make middleware establish identity, then enforce permission for the exact case at the service boundary.",
        code='''from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from .models import PermitCase


@login_required
def permit_detail(request, case_id: int):
    permit = (
        PermitCase.objects.filter(
            pk=case_id, allowed_reviewers=request.user
        )
        .values("id", "title", "status")
        .first()
    )
    if permit is None:
        raise Http404()
    return JsonResponse(permit)''',
        checks=["Session state is prepared before authentication resolves the user.", "An authenticated reviewer still needs permission for this case.", "Forbidden and missing private cases obey one disclosure rule."],
        mistakes=["Using login status as permission for every object.", "Placing session-dependent middleware before its prerequisite.", "Checking permission in one view but omitting it from another service caller."],
        related=["web-tech/authorization-and-tenant-boundaries", "web-tech/federated-identity-and-session-lifecycle"],
    ),
    dict(
        slug="django-queryset-shape-prefetch-and-page-cost",
        title="Django QuerySet Shape, Prefetch, and Page Cost",
        summary="Bound query count, transferred columns, page width, and relation loading for a case list.",
        concept="A QuerySet describes work until evaluation asks the database for results. That delay is useful, but it makes an innocent-looking template or serializer capable of issuing a query per row. For a foreign-key district on a permit, select_related can fetch the single-valued relation with a join. For attachments, prefetch_related performs a separate batch query and attaches the many-valued rows to the selected parents. Neither call means every relation should be loaded by default. A useful list has an explicit authorization filter, stable order, selected relation shape, and page limit. Its cost is the rows and objects actually materialized, plus the database work required to find them.",
        case="A reviewer queue lists 47 permits, their districts, and attachment names. The first version fetches permits and then accesses each district and attachment collection while rendering. Its query count grows with the page. The next version prefetches every attachment for an unbounded 47,000-case result, reducing query count while exhausting application memory. A third version paginates with a very high offset and becomes slow even though the page has only 47 rows. The repaired queue filters by reviewer, applies a deterministic created-at and ID order, slices before evaluation, and loads only relations shown on this screen. A cursor avoids repeatedly walking deep offsets.",
        implementation="Start with a permission-scoped base QuerySet. Use select_related for the district foreign key because each case has at most one district. Use prefetch_related for attachments only when this view actually displays them, and select the attachment columns needed by a compact summary if the full model is too large. Apply a deterministic order with an ID tie breaker and fetch at most 47 rows. For continuation, encode a server-validated cursor from the final ordering key rather than accepting an arbitrary raw SQL fragment. A simple slice works for an initial page; a deep feed should use keyset conditions that match the order. Materialize once, then serialize without accidental relation access.",
        cost="The initial list evaluates at most 47 parent rows, so response memory is O(page size plus selected attachments). A many-valued prefetch issues another query and can still transfer many attachment rows per case; cap or summarize them if collections are large. A join for a single-valued relation avoids repeated queries but increases row width. Counting all matching rows for every page adds a separate potentially expensive operation. High-offset pagination can scan or discard many earlier rows in the database, even though Python receives only one page. Cursor pagination changes the client contract but supports indexed continuation. Inspect query counts, transferred bytes, plan shape, and p95 latency with realistic assignment sizes.",
        failure="Render 47 cases with a query counter and compare the unoptimized and planned versions. Include a case with no attachments and one with many; neither should silently trigger an extra per-row lookup. Change two creation timestamps to the same value and ensure the ID tie breaker prevents duplicates or omissions across pages. Request a cursor outside the user's scope and make sure filtering remains in force. Test a deep offset to demonstrate its database cost before replacing it. Verify a screen that does not display attachments does not prefetch them. Confirm serialization cannot reach a deferred relation that reintroduces hidden work.",
        drill="Build a 47-row reviewer queue and seed enough cases to make the old high-offset path measurable. Record SQL query count and rows returned while rendering district and attachment summaries. Add select_related and a bounded prefetch, then repeat the measurement. Remove the attachment panel and remove its prefetch too. Introduce duplicate timestamps, implement an ID tie breaker, and write continuation tests that traverse pages without repeats. Compare a deep offset with a keyset continuation under the same authorization predicate. Document whether an exact total count is truly needed by the product.",
        decision="Choose relation loading after fixing the page and permission scope; optimize measured query and row costs together.",
        code='''from django.db.models import Prefetch
from .models import PermitAttachment, PermitCase


def reviewer_queue(reviewer_id: int):
    attachments = PermitAttachment.objects.only("id", "case_id", "name")
    cases = (
        PermitCase.objects.filter(allowed_reviewers__id=reviewer_id)
        .select_related("district")
        .prefetch_related(Prefetch("attachments", queryset=attachments))
        .order_by("-created_at", "-id")[:47]
    )
    return list(cases)''',
        checks=["The reviewer filter survives every page and cursor.", "Only displayed relations are joined or prefetched.", "Ordering stays stable when timestamps are equal."],
        mistakes=["Prefetching an unbounded result set to eliminate query count alone.", "Assuming a high offset costs only the returned page.", "Using a timestamp without a unique tie breaker for continuation."],
        related=["web-tech/data-persistence", "web-tech/database-capacity-and-online-change-operations"],
    ),
    dict(
        slug="django-form-csrf-atomic-approval-and-on-commit",
        title="Django Forms, CSRF, Atomic Approval, and On-Commit Work",
        summary="Validate a browser command, commit one state change, and dispatch side effects after commit.",
        concept="A browser form that mutates state crosses several independent boundaries. CSRF protection checks that a same-origin user action is not silently forged through the browser's ambient credentials. Form validation checks the submitted fields. Authorization checks the current reviewer and case relationship. A database transaction protects the state transition from partial writes. None of these substitutes for the others. A retry after a lost response can still repeat an already committed action unless the command carries a stable idempotency key stored under a unique constraint. Notification dispatch belongs after the transaction commits, because a sent notification for rolled-back work is a lie.",
        case="Reviewer 47 approves case 62 through a POST form. The browser times out after the database commit and the reviewer presses Submit again. A naive handler adds a second audit entry and sends another notification. In a separate failure, the notification queue accepts a message before a later validation error rolls back the approval. The corrected handler requires the page's CSRF token, validates the operation key and requested transition, locks and authorizes the case inside one transaction, and records the operation under a uniqueness rule. It schedules a notification only for a newly created approval and only after a successful commit. A replay returns the saved outcome.",
        implementation="Keep CSRF middleware enabled and include the token in the rendered POST form; API clients with another authentication model need an explicit policy rather than a blanket exemption. Reject an empty or malformed operation ID. In a synchronous service, open atomic, select the case for update on a database that supports row locking, verify reviewer permission and transition state, and insert the outcome with a unique operation key. The unique constraint is the final defense against concurrent replays. Register on_commit after the new operation is recorded. The callback should enqueue a durable event or outbox dispatcher, not be the sole proof that a notification exists; an application crash just after commit can still lose an in-process callback.",
        cost="The transaction holds locks while it validates and writes. Keep network calls outside that lock; waiting for a remote mail service under atomic expands contention and slows unrelated reviewers. A unique index and retained operation records use storage proportional to kept commands, with a retention policy tied to realistic retry windows. A row lock serializes conflicting approvals for one case, which is often the intended behavior, but a hot case can create queueing. CSRF validation adds modest request work and prevents a different class of browser-origin attack than authorization. Measure lock wait, duplicate-command rate, callback lag, and the gap between approval commit and durable notification acceptance.",
        failure="Submit without a CSRF token and confirm the browser form is rejected before mutation. Send a valid token as reviewer 81 for case 62 and confirm authorization still fails. Race two requests with the same operation ID; only one logical approval and one durable event should remain. Commit successfully, drop the HTTP response, and retry with the same ID to recover the prior result. Force an exception after updating the case but before commit and ensure the state and event both roll back. Crash the process after commit and before a callback runs in a fault test; this exposes why the durable outbox is necessary.",
        drill="Implement an approval form, command service, operation table, and notification outbox for one permit. Write the database uniqueness and case status constraints before the view. Exercise missing token, malformed ID, forbidden reviewer, stale status, exact replay, and simultaneous replay. Use on_commit to wake the outbox dispatcher only after commit; store the event itself in the same transaction as the approval. Observe the callback timing in tests that commit and in tests that roll back. Explain the remaining retention and delivery decisions in the project's operational notes.",
        decision="Treat CSRF, permission, transaction, replay identity, and durable side effects as separate checks on one command.",
        code='''from django.db import transaction
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .services import approve_once, wake_approval_outbox


@require_POST
@login_required
def approve_permit(request, case_id: int):
    operation_id = request.POST.get("operation_id", "")
    if not operation_id or len(operation_id) > 81:
        return JsonResponse({"error": "Invalid operation"}, status=400)
    with transaction.atomic():
        outcome = approve_once(
            reviewer_id=request.user.id,
            case_id=case_id,
            operation_id=operation_id,
        )
        if outcome is None:
            raise Http404()
        if outcome.created:
            transaction.on_commit(wake_approval_outbox)
    return JsonResponse({"status": outcome.status})''',
        checks=["CSRF rejection occurs before a browser mutation.", "The service owns a unique operation key and current permission check.", "The durable event commits with the approval; the callback only wakes delivery."],
        mistakes=["Disabling CSRF because a user is authenticated.", "Queuing a notification before its database state commits.", "Treating on_commit alone as durable message storage."],
        related=["web-tech/api-mutation-and-failure-contracts", "web-tech/background-workflow-reliability"],
    ),
    dict(
        slug="django-asgi-async-view-and-sync-orm-boundary",
        title="Django ASGI, Async Views, and the Sync ORM Boundary",
        summary="Use asynchronous views where waiting overlaps, while keeping transactional database work synchronous.",
        concept="An async view can await nonblocking work while an ASGI server handles other connections. That property does not make a blocking database call or CPU-heavy transformation safe on the event loop. Django offers asynchronous variants for many ORM operations, but transactions remain a synchronous boundary in current releases. A function that must lock and commit several rows belongs in one synchronous service called through sync_to_async. The bridge should wrap the whole unit, not one ORM call at a time. Synchronous middleware in an otherwise async request path can require a thread adaptation and reduce the expected concurrency gain. Choosing ASGI therefore depends on the application's actual waiting behavior, not on the presence of async keywords.",
        case="A permit queue view becomes async because it also waits for a remote jurisdiction status service. Its author reads request.user lazily and calls a synchronous QuerySet directly; the request fails with an async-safety error. A later patch wraps three individual database calls, but the approval transaction is split across awaits and can no longer act as one unit. The repaired read view obtains the user through the async authentication API, bridges once to a synchronous, permission-scoped list service, and awaits the external status call with a deadline. The approval write stays in a separate synchronous transactional service. Only measured overlapping I/O justifies operating this path under ASGI.",
        implementation="Use an ASGI application server for the async request path and verify the deployed middleware stack; mixing synchronous middleware can force adaptation. In an async view, await request.auser before reading the authenticated user. Reject an anonymous caller, then call a bounded synchronous service with sync_to_async and thread_sensitive enabled. That service evaluates its QuerySet and returns plain serializable values, so lazy ORM work cannot escape into the async view. Place an explicit timeout around the external network call and define what happens if it fails. For a multi-row approval, keep atomic and on_commit inside one synchronous service. Do not enable an unsafe override to silence an async-safety exception.",
        cost="ASGI can improve throughput when many requests spend time awaiting genuinely async I/O. A synchronous database bridge still consumes thread capacity and a context switch. Wrapping each model access separately multiplies that overhead and can leak lazy query evaluation into an unsafe context. Fetching 47 summaries at once bounds memory and keeps one permission scope. A remote call needs a deadline, concurrency limit, and fallback contract; without them an async route can accumulate many suspended requests and exhaust downstream capacity. Track event-loop lag, bridge calls per request, thread saturation, external latency, and middleware adaptation before deciding that this path is faster than a conventional synchronous view.",
        failure="Run the view with anonymous and assigned users. Confirm anonymous access stops before the case query. Deliberately access request.user and evaluate a synchronous QuerySet in an async view in a test, observe the async-safety failure, and restore the safe boundary. Return a lazy QuerySet from the bridged service and show why JSON serialization can trigger work later; replace it with realized dictionaries. Delay the remote status service past its deadline and verify a bounded response. Compare ASGI behavior with a synchronous middleware layer present and removed. Race two approvals to confirm that the separate synchronous transaction still owns the write invariant.",
        drill="Create an async read endpoint that combines a local authorized case list with a remote jurisdiction status. Set a 47-row limit and a finite remote timeout. Place all synchronous ORM evaluation in one service and call it through a single thread-sensitive bridge. Return primitive dictionaries, not models or QuerySets. Measure bridge count and event-loop lag under simultaneous requests. Then implement a distinct synchronous approval service with atomic state and event recording. Test cancellation and timeout, and record which operations can be safely retried after the client loses its response.",
        decision="Use async for overlapping waits; keep transactional ORM work in one synchronous function and bridge at that boundary.",
        code='''from asgiref.sync import sync_to_async
from django.http import JsonResponse
from .services import list_authorized_permits


async def permit_queue(request):
    reviewer = await request.auser()
    if not reviewer.is_authenticated:
        return JsonResponse({"error": "Sign in required"}, status=401)
    rows = await sync_to_async(
        list_authorized_permits, thread_sensitive=True
    )(reviewer.id, limit=47)
    return JsonResponse({"cases": rows})''',
        checks=["Lazy authentication and ORM evaluation never run synchronously on the event loop.", "One bridge returns materialized, permission-scoped values.", "A multi-row transaction remains inside one synchronous service."],
        mistakes=["Calling a synchronous QuerySet directly inside an async view.", "Returning lazy models from the bridge for later serialization.", "Adding async syntax without measuring actual waiting or middleware adaptation."],
        related=["web-tech/backend-api-systems", "web-tech/request-deadlines-retries-and-backoff"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/express-request-and-process-boundaries"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Build Django request paths with exact permissions, bounded ORM reads, safe browser commands, and async boundaries.",
           sort_order=3710, created_at=stamp, updated_at=stamp, published_at=stamp)
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
                 title=topic["title"], summary=topic["summary"], sort_order=3711 + number,
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
hub["body"] = paragraph("A Django permit service must carry a reviewer's identity into an exact case permission check, read only a bounded queue, commit browser commands once, and keep synchronous database transactions outside the async event loop. These lessons use one set of permit cases so query shape, retry behavior, and deployment choices can be evaluated against the same business rule.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/backend-api-systems", "web-tech/authorization-and-tenant-boundaries", "web-tech/data-persistence"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"],
                                       "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/backend-api-systems": [hub_path],
    "web-tech/authorization-and-tenant-boundaries": ["web-tech/django-middleware-session-and-object-permissions"],
    "web-tech/data-persistence": ["web-tech/django-queryset-shape-prefetch-and-page-cost"],
    "web-tech/api-mutation-and-failure-contracts": ["web-tech/django-form-csrf-atomic-approval-and-on-commit"],
    "web-tech/server-rendering-and-client-data-flow": ["web-tech/django-asgi-async-view-and-sync-orm-boundary"],
}
for path, targets in crosslinks.items():
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4,
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))

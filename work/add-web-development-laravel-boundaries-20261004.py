"""Add original Laravel authorization, query, transaction, and queue lessons."""
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
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/laravel-policy-query-and-queue-boundaries"
hub_title = "Laravel Policy, Query, and Queue Boundaries"
topics = [
    dict(
        slug="laravel-route-binding-policy-and-private-resource-scope",
        title="Laravel Route Binding, Policy, and Private Resource Scope",
        summary="Treat route binding as lookup, then evaluate permission for the resolved case and every write.",
        concept="Laravel route model binding turns a route identifier into a model instance. That removes lookup boilerplate, but the bound model is only a lookup result. A matching case ID does not prove the signed-in reviewer may see it. A policy expresses an action against a specific model and caller; the controller or route must invoke that policy before returning private fields. For a private resource, a policy can deliberately make a denied case appear missing so a guessed ID does not reveal existence. The same authorization rule must cover exports and state changes. A successful GET authorization is not a durable grant for a later POST after assignments or case status change.",
        case="Reviewer 47 can inspect permit 62. Reviewer 81 sees another queue, guesses 62 in the address bar, and receives a bound PermitCase because the route accepts any existing primary key. A detail endpoint that serializes the whole model then exposes internal district notes. Adding an auth middleware stops anonymous callers, but reviewer 81 remains signed in. The repaired route invokes a view policy on the bound case and returns only a deliberate resource projection. Export metadata uses the same policy. Approval calls a current-state service that checks the reviewer's assignment inside the write transaction, because a previously authorized screen may be stale.",
        implementation="Keep authentication middleware on private routes and register the policy for the PermitCase model. Make the view rule inspect the current reviewer-to-case mapping and return a denial shaped by the product's existence-disclosure rule. Invoke authorization before constructing a response resource or starting an export. Do not rely on a controller's menu filtering or client-hidden button. For nested routes, scoped bindings can constrain children to their parent relationship, but they do not replace a user policy. In the mutation service, re-read the case under a lock and verify the caller and requested transition again. Return a narrow resource rather than every database column. Record a request identifier for support without including hidden titles in client errors.",
        cost="Authentication, model binding, and a policy lookup each can perform database work. A policy that walks a lazy relationship on every list row creates repeated queries; list endpoints should instead apply a permission-scoped base query and avoid authorizing hundreds of hydrated models one by one when the policy can be represented in SQL. A targeted detail lookup usually needs only one indexed assignment check. Denying private resources as missing may make client diagnostics less obvious, so capture a safe internal reason and request ID. Measure query count for allowed, forbidden, and missing IDs, plus the time spent in policy evaluation under large reviewer assignments.",
        failure="Call the bound route anonymously, as reviewer 47, as reviewer 81, and with an unknown ID. The forbidden and unknown responses should follow the same chosen disclosure policy. Add an export route and verify it cannot bypass the view rule. Remove the policy invocation in a negative test and observe the guessed-ID leak, then restore it. Revoke reviewer 47's assignment after a detail GET and attempt approval; the service must reject the now-stale permission. Return a model with private notes from a negative test and verify the resource projection excludes them. Watch for extra relationship queries when policies run across a queue.",
        drill="Implement detail, export metadata, and approval routes for a permit workflow. Seed cases 62 and 81 with disjoint reviewers. Write the PermitCase view and approve policy rules, choosing whether a forbidden detail should be 403 or private 404. Use route binding for the detail page, then add an explicit policy check and a response resource. Implement approval in a service that reevaluates current permission under a transaction. Add tests for guessed IDs, revoked assignment, and a list of 47 cases. Record query counts and prove that private model attributes never enter the public response.",
        decision="Let binding locate the case; let a policy and current-state service decide whether that reviewer may use it.",
        code='''<?php
use App\\Http\\Resources\\PermitResource;
use App\\Models\\PermitCase;
use Illuminate\\Support\\Facades\\Gate;
use Illuminate\\Support\\Facades\\Route;

Route::middleware('auth')->get('/permits/{permit}', function (PermitCase $permit) {
    Gate::authorize('view', $permit);

    return new PermitResource($permit);
});''',
        checks=["A bound model is still checked against the current reviewer.", "Export and mutation entry points repeat their required action checks.", "Public resources exclude internal case fields."],
        mistakes=["Treating route model binding as permission.", "Checking only whether a reviewer is signed in.", "Returning the entire model after a successful policy check."],
        related=["web-tech/authorization-and-tenant-boundaries", "web-tech/django-middleware-session-and-object-permissions"],
    ),
    dict(
        slug="laravel-eloquent-loading-and-cursor-page-cost",
        title="Laravel Eloquent Loading and Cursor Page Cost",
        summary="Shape a reviewer queue with scoped SQL, needed relations, stable order, and bounded pages.",
        concept="Eloquent relationship properties may issue database queries when accessed, so a template that displays a relation for each case can turn one queue query into many. Eager loading requests needed relations with the parent query and prevents those per-row lookups. That is not a license to load every attachment for every case. A reviewer queue must first restrict rows to the caller, then choose the fields and relation summaries shown on one page. Cursor pagination uses ordered values to continue through large results without walking an ever-growing offset. Its order needs a unique tie breaker and database support from suitable indexes; it cannot promise an exact numbered page count.",
        case="A municipal queue renders 47 permits with district names and attachment counts. The first implementation fetches permits and lazily reads each district and attachments collection. Query count rises with the page. The second eagerly loads every attachment for 47,000 permits to silence the query counter and strains memory. A third uses an offset near the end of the queue; response width is small, yet the database spends time skipping earlier rows. The repaired query scopes by reviewer, selects a 47-row cursor page, eager loads the one district name actually rendered, obtains attachment counts without loading all attachment models, and orders by created_at plus a unique case ID.",
        implementation="Start with the authorization predicate in the SQL builder; do not filter another reviewer's cases in PHP after reading them. Use with for the displayed district relation and withCount for attachment totals when the actual attachment records are not shown. Order by a non-null creation field and ID, then cursorPaginate the fixed page width. Include foreign keys needed by selected relations and avoid selecting so few columns that hydration triggers unexpected work. Cursor values must remain part of the same reviewer-scoped query; a client cursor is navigation state, not permission. Where a screen needs numbered pages and totals, choose another pagination contract and accept its count and offset costs deliberately.",
        cost="A bounded page uses O(page size) parent memory, plus only the selected related district rows. withCount adds SQL work but avoids materializing every attachment. Eager loading a many-valued relation can still transfer thousands of children, so measure row count and payload size as well as query count. Offset pagination can spend work proportional to the skipped rows; an indexed cursor often improves deep continuation. A cursor does not provide a cheap exact total or stable page number, and inserts can change what appears between requests. Track database plan, p95 latency, query count, transferred bytes, and memory for both sparse and attachment-heavy cases.",
        failure="Seed 47 cases with repeated created_at values and verify ID ordering traverses without duplicates. Add a case with hundreds of attachments; the list must display its count without hydrating those records. Remove eager loading and inspect the N+1 queries produced by district access, then restore it. Try a deep offset on a large fixture and compare its query plan with cursor continuation. Submit a cursor while changing reviewer identity and ensure the SQL permission predicate still applies. Ask a list serializer for a relation it did not preload and catch the lazy load in a controlled test before that behavior reaches production.",
        drill="Build a reviewer queue with district labels, attachment totals, and a 47-case page limit. Instrument query count and SQL time before optimization. Add the reviewer scope in the query, then with and withCount only for displayed data. Give several cases the same timestamp, add an ID tie breaker, and implement next-page navigation. Compare cursor and offset behavior at a deep position with an index on the chosen order. Remove an eager load in a negative test and show the query count change. Explain whether the product truly needs an exact total or numbered page links.",
        decision="Scope the data first, then optimize the bounded response for both query count and transferred rows.",
        code='''<?php
use App\\Models\\PermitCase;

$queue = PermitCase::query()
    ->whereHas('reviewers', fn ($reviewers) => $reviewers->whereKey($reviewer->id))
    ->with('district:id,name')
    ->withCount('attachments')
    ->orderByDesc('created_at')
    ->orderByDesc('id')
    ->cursorPaginate(47);''',
        checks=["The reviewer filter remains on every page.", "Attachment counts do not load attachment models.", "Timestamp ties are broken by a unique case ID."],
        mistakes=["Fixing N+1 by loading an unbounded result set.", "Assuming a deep offset costs only 47 rows.", "Using a cursor order without a unique tie breaker."],
        related=["web-tech/data-persistence", "web-tech/django-queryset-shape-prefetch-and-page-cost"],
    ),
    dict(
        slug="laravel-form-request-transaction-and-approval-replay",
        title="Laravel Form Requests, Transactions, and Approval Replay",
        summary="Validate a browser command, lock current state, commit once, and recover an ambiguous retry.",
        concept="A form request validates HTTP input before a controller processes it. Browser CSRF middleware checks a different boundary: whether a credentialed browser request carries the expected token. A policy decides whether the current reviewer may change this case. A database transaction then makes the state transition and audit record one unit. These checks cannot substitute for each other. A lost HTTP response after commit leaves the client uncertain; a stable operation ID and database uniqueness rule let a retry recover the committed outcome instead of repeating the approval. Deadlock retry can rerun the transaction closure, so external email and other irreversible effects do not belong inside it.",
        case="Reviewer 47 submits approval for case 62 from a form. The server commits but the connection drops before the browser sees the response. The browser retries. Without a command key, the service writes a second audit event and sends another notice. In another path, reviewer 81 submits a valid form for the same case; validation succeeds, but the approval must still be denied. The repaired command has a bounded operation ID and expected revision, checks current assignment under a row lock, and stores the outcome under a unique key. The transaction commits the case transition and outbox intent together. A retry with the same key returns the original result.",
        implementation="Use the web route's CSRF middleware and include a token in the actual form template. Put syntactic field limits in an ApprovePermitRequest, including operation ID shape and revision range. The controller should obtain reviewer identity from the authenticated request, not the body. Delegate to a service that starts a transaction, locks the case where supported, checks current permission and revision, and writes the operation and outbox event under database constraints. A duplicate operation should return the stored result if its original command fields match; the same key with different fields is a conflict. If deadlock retry is enabled, ensure the closure has only transactional database effects and is safe to execute again.",
        cost="Row locking serializes conflicting approvals for one case and can create wait time on a hot permit. A uniqueness index and retained operation records consume storage proportional to the replay window, and the outbox adds a row per accepted state change. Form validation and CSRF checks are modest compared with database work but reject bad browser traffic before a lock is taken. Deadlock retries may repeat reads and writes, increasing tail latency; they do not guarantee success and should be bounded. Measure lock wait, transaction duration, duplicate-key conflicts, rejected CSRF requests, and the time between approval commit and durable notification acceptance.",
        failure="Post the browser form without a CSRF token, then with a valid token but reviewer 81; neither may mutate case 62. Send an invalid operation ID and a stale revision. Race two approvals with the same ID and assert one case transition, one audit operation, and one outbox event. Commit an approval, discard its HTTP response, and replay the same ID to recover the prior result. Retry the same ID with a different reason and require a conflict. Force a database exception after changing status; the outbox and status must both roll back. Trigger a deadlock retry in a test and confirm no email is sent from inside the retried closure.",
        drill="Implement a form request, approval controller, service, unique operation table, and notification outbox. Seed reviewer 47 and reviewer 81 with different assignments. Write expected responses for missing token, malformed command, forbidden case, stale revision, exact replay, and changed-payload replay before coding. Execute the approval through an explicit transaction and only build the public response after commit. Add a fault injection immediately before the outbox insert and another after commit but before response delivery. Use the stable command key to show which state can be recovered by retry and which requires operator inspection.",
        decision="Validate the browser command, authorize current state, and commit an idempotent database outcome before reporting success.",
        code='''<?php
use App\\Http\\Requests\\ApprovePermitRequest;
use App\\Models\\PermitCase;
use App\\Services\\ApprovalService;
use Illuminate\\Http\\JsonResponse;
use Illuminate\\Support\\Facades\\DB;

final class ApprovePermitController
{
    public function __invoke(
        ApprovePermitRequest $request,
        PermitCase $permit,
        ApprovalService $approvalService,
    ): JsonResponse {
        $outcome = DB::transaction(
            fn () => $approvalService->approveOnce(
                $request->user()->id,
                $permit->id,
                $request->validated(),
            ),
            attempts: 3,
        );

        return response()->json(['case_id' => $outcome->caseId, 'status' => $outcome->status]);
    }
}''',
        checks=["CSRF and field validation stop malformed browser commands.", "The service owns current permission, uniqueness, and transaction state.", "A replay returns one committed outcome without a second event."],
        mistakes=["Treating valid form fields as authorization.", "Sending email inside a deadlock-retried transaction closure.", "Using a client-generated reviewer ID as trusted identity."],
        related=["web-tech/api-mutation-and-failure-contracts", "web-tech/django-form-csrf-atomic-approval-and-on-commit"],
    ),
    dict(
        slug="laravel-after-commit-jobs-and-outbox-recovery",
        title="Laravel After-Commit Jobs and Outbox Recovery",
        summary="Dispatch after database commit while retaining durable intent when a queue hint is lost.",
        concept="A queued job can begin before the transaction that produced its input commits unless dispatch is coordinated with commit. Laravel can delay a dispatch until after commit, which stops a worker from reading a row that is still invisible or will be rolled back. That timing guarantee is not the same as durable intent. A process can fail after the database commits but before the queue receives the job. For a notification promised by a permit approval, write an outbox row in the same transaction as the case change. An after-commit job can wake a dispatcher, and a scheduled sweep can find events whose wake-up never arrived. The worker must handle retry and ambiguous provider outcomes by event identity.",
        case="Case 62 is approved and a job is dispatched inside the transaction. A fast worker reads before commit and cannot find the new approval. Moving dispatch to after commit fixes the visibility race. Then the API process crashes immediately after commit, before its queued wake-up reaches a broker. The notification still disappears if dispatch was the only record of work. The repaired command stores event 93 in an outbox table with the approval. The queued job carries only that event ID and can be lost without losing the intent. A worker or periodic sweep claims the row, sends with a stable provider key when possible, and records the outcome.",
        implementation="Write the outbox event, recipient policy, and case state in one database transaction. Dispatch a short wake-up job with afterCommit, or configure the queue connection to defer all relevant jobs; make that choice explicit in deployment settings. Give the job only stable identifiers, not a model snapshot whose authorization or recipient state may become stale. The dispatcher claims pending events under a lease or atomic state transition, uses a provider idempotency key if available, and records delivery or retry state. Give workers finite attempt and timeout budgets and a dead-letter path for permanent failures. Scan pending events independently of the wake-up path so a post-commit process crash is recoverable.",
        cost="An outbox insert adds transaction work and storage, while a sweep and worker pool consume database reads and queue capacity. After-commit dispatch avoids uncommitted-row races but may add a small delay before workers start. Retry can duplicate external effects when the provider accepted a message but the acknowledgment was lost; an event identity or provider key narrows that ambiguity. Unique-job locks prevent some duplicate dispatches but are not permanent exactly-once delivery guarantees. Monitor oldest pending event, lease expirations, retry count, provider response class, and queue lag. Do not measure success only by the API response or by a job being enqueued.",
        failure="Roll back approval and verify neither the outbox event nor after-commit wake-up is visible. Commit approval, kill the API process before dispatch, restart the sweep, and confirm the event is found. Process one event twice and require one durable delivered state; inspect whether the provider itself can deduplicate a repeated send. Crash a worker after claiming but before acknowledging and confirm the lease expires. Force a permanent invalid recipient and move the event to a reviewable failure state instead of retrying forever. Deploy without queue workers and verify monitoring exposes the growing pending age promptly.",
        drill="Implement an approval outbox row and a WakePermitOutbox job. Have the controller dispatch after commit, while a scheduled worker scans at most 47 pending rows per batch. Use event 93 as a stable identity distinct from the HTTP request ID. Test rollback, post-commit crash, queue delay, provider timeout after possible acceptance, lease expiry, and permanent failure. Record enough state to answer whether a reviewer notification was pending, attempted, delivered, or needs intervention. Verify the job acquires its own database resources and cannot reuse a request transaction after the response.",
        decision="Use after-commit dispatch for ordering and a transactional outbox for recovery when dispatch itself is lost.",
        code='''<?php
use App\\Jobs\\WakePermitOutbox;
use App\\Models\\ApprovalOutbox;
use App\\Models\\PermitCase;
use Illuminate\\Support\\Facades\\DB;
use Illuminate\\Support\\Facades\\Gate;

$eventId = DB::transaction(function () use ($caseId, $reviewer) {
    $permit = PermitCase::query()->whereKey($caseId)->lockForUpdate()->firstOrFail();
    Gate::forUser($reviewer)->authorize('approve', $permit);
    $permit->status = 'approved';
    $permit->save();

    $event = ApprovalOutbox::query()->create([
        'case_id' => $caseId,
        'reviewer_id' => $reviewer->id,
        'kind' => 'permit_approved',
        'state' => 'pending',
    ]);

    WakePermitOutbox::dispatch($event->id)->afterCommit();
    return $event->id;
});''',
        checks=["The approval and outbox row commit or roll back together.", "Wake-up dispatch waits until commit.", "A sweep can recover a pending row when dispatch is lost."],
        mistakes=["Treating afterCommit as a durable outbox.", "Assuming queue uniqueness means external delivery happened exactly once.", "Retrying provider failures without a stable event identity."],
        related=["web-tech/background-workflow-reliability", "web-tech/fastapi-lifespan-background-work-and-delivery-state"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/fastapi-contract-and-resource-boundaries"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Build Laravel permit services with model policy checks, bounded Eloquent reads, replay-safe writes, and recoverable jobs.",
           sort_order=3730, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    subprocess.run(["php", "-l"], input=topic["code"], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3731 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-php">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
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
hub["body"] = paragraph("A Laravel permit service binds a case from a route, checks a reviewer's permission, reads a bounded queue, commits a retry-safe approval, and delivers its notification after the database state exists. These lessons keep the same case and reviewer identities across boundaries so a passing route cannot hide an unscoped model lookup, costly relation loading, duplicate write, or lost queue dispatch.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/backend-api-systems", "web-tech/authorization-and-tenant-boundaries", "web-tech/data-persistence"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"],
                                       "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/backend-api-systems": [hub_path],
    "web-tech/authorization-and-tenant-boundaries": ["web-tech/laravel-route-binding-policy-and-private-resource-scope"],
    "web-tech/data-persistence": ["web-tech/laravel-eloquent-loading-and-cursor-page-cost"],
    "web-tech/api-mutation-and-failure-contracts": ["web-tech/laravel-form-request-transaction-and-approval-replay"],
    "web-tech/background-workflow-reliability": ["web-tech/laravel-after-commit-jobs-and-outbox-recovery"],
    "web-tech/fastapi-contract-and-resource-boundaries": [hub_path],
}
for path, targets in crosslinks.items():
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4,
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))

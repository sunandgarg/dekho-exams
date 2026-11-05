"""Add original Rails request, query, transaction, and job boundary lessons."""
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


hub_path = "web-tech/rails-request-record-and-job-boundaries"
hub_title = "Rails Request, Record, and Job Boundaries"
topics = [
    dict(
        slug="rails-controller-parameters-and-object-permission",
        title="Rails Controller Parameters and Object Permission",
        summary="Permit command fields narrowly, then authorize the exact case before projecting a response.",
        concept="Strong parameters limit which submitted attributes may reach model assignment. They do not identify the caller, verify the caller's permission for a record, or decide whether a state transition is legal. A Rails controller should derive identity from its authenticated server session, scope the requested record to that identity, and pass a narrow command to a service. A route ID is an address, not a grant. Browser CSRF protection checks whether a credentialed mutation carries the expected authenticity token; it does not replace case-level permission. The response deserves a separate projection so an authorized view does not accidentally disclose every model column or association.",
        case="Reviewer 47 opens permit 62, while reviewer 81 guesses its URL. Both have valid accounts. A controller calls PermitCase.find(params[:id]), permits the submitted status field, and renders the model as JSON. Reviewer 81 can read a private district note; a later forged form can set status directly because the controller confuses a permitted field with an allowed action. A navigation menu filtered by reviewer hid the case, but it never protected the route. The repaired controller loads case 62 from a reviewer-scoped relation, sends only operation ID and reason to an approval service, and returns a deliberate case ID and status. The service checks current assignment again when it writes.",
        implementation="Apply an authentication guard to private actions and keep request forgery protection active for cookie-backed browser mutations. Require the expected command envelope and permit only its defined keys; reject missing or malformed values before using them. Do not permit reviewer_id, case_id, or status from the browser for an approval action. Load detail and export metadata through the same record scope, then render an explicit output hash or serializer with approved fields. For a private case, choose whether forbidden and nonexistent IDs share a missing-style response so ID guessing reveals no existence signal. Passing a scoped relation into a service is safer than fetching globally and relying on every downstream caller to remember a second filter.",
        cost="An assignment-scoped detail lookup adds a join or existence predicate and needs indexes on case and reviewer IDs. This is a small, measurable price for preventing cross-account reads. A policy implemented by lazy-loading an assignment on each item of a 47-case list adds many queries; list authorization belongs in SQL before pagination. Explicit projections reduce transferred bytes and keep private attributes out of serialization even after permission succeeds. CSRF verification and parameter shape checks are cheap compared with database work, and they can reject hostile browser commands before locks are taken. Track query count, response width, forbidden/missing timing, and rejected command classes. A 404 policy should not hide security failures from internal incident logs.",
        failure="Make requests anonymously, as reviewer 47, as reviewer 81, and with an unknown permit ID. Confirm the forbidden and unknown responses match the product's disclosure rule. Put an obvious private_note on permit 62 and assert it never enters detail or export JSON. Submit a form with a valid authenticity token but reviewer 81's session; it must still fail the case permission check. Submit an invalid token while signed in as reviewer 47 and verify the controller does not reach the service. Try mass assignment with status, reviewer_id, and an internal flag in the approval body; none should enter the command. Revoke reviewer 47's assignment between GET and POST and confirm the write is rejected.",
        drill="Create a private permit controller for reviewer 47 and reviewer 81. Seed case 62 with one owner, one permitted reviewer, and a private note. The show action should scope by current reviewer and project only public title, case ID, and status. The approval action should accept a stable operation ID, expected revision, and bounded reason; it must never accept status or reviewer identity from params. Wire a browser form with the authenticity token and keep the non-GET protection active. Write request tests for guessed IDs, a missing record, missing token, extra attributes, and assignment revocation. Inspect actual SQL from the scoped relation and add indexes that match the join used by the route.",
        decision="Strong parameters define a command shape; server identity, record scope, and current transition rules decide permission.",
        code='''class PermitsController < ApplicationController
  before_action :require_reviewer

  def show
    permit = PermitCase.joins(:reviewer_assignments)
      .where(reviewer_assignments: { reviewer_id: Current.reviewer.id })
      .find(params[:id])

    render json: { case_id: permit.id, title: permit.title, status: permit.status }
  end

  private

  def approval_params
    params.require(:approval).permit(:operation_id, :expected_revision, :reason)
  end
end''',
        checks=["A signed-in reviewer is still scoped to the exact permit.", "Only named command fields can enter the approval service.", "The public response omits private model attributes."],
        mistakes=["Treating permitted parameters as permission to approve.", "Authorizing a menu while leaving a detail route unscoped.", "Rendering an entire model after an access check."],
        related=["web-tech/authorization-and-tenant-boundaries", "web-tech/django-middleware-session-and-object-permissions", "web-tech/laravel-route-binding-policy-and-private-resource-scope"],
    ),
    dict(
        slug="rails-active-record-scope-eager-load-and-page-cost",
        title="Rails Active Record Scope, Eager Load, and Page Cost",
        summary="Scope and bound a review queue, load only displayed relations, and preserve a deterministic order.",
        concept="Active Record relations defer SQL until a result is needed. That makes composition useful, but a template can silently trigger more SQL when it reads an unloaded association on every row. A permit queue must first constrain rows to the current reviewer, then choose the page width and only the related data visible on that page. Eager loading addresses repeated association reads; it does not justify loading every attachment into memory. The order must be deterministic when timestamps tie. A keyset cursor combines the last ordered values with the same scope predicate; merely returning an opaque cursor does not authorize the next page.",
        case="The first permit board asks for 47 cases and displays each district name. Its initial query is fast, but 47 lazy district reads follow. A second version calls includes(:district, :attachments) for a page whose one case has 620 scans. Query count falls while response memory and transfer size jump. A third version uses offset 47000; the database spends work locating and skipping rows before it returns the next 47. The repaired queue filters assignments in SQL, caps the parent page, preloads the district only, obtains attachment totals from a count projection or maintained counter, and orders by created_at plus ID. Each continuation keeps the reviewer predicate.",
        implementation="Start with a relation constrained by reviewer assignment. Select a bounded page before rendering, and use includes or preload for the district relation actually shown. A counter cache is useful only when its update and reconciliation rules are reliable; otherwise a grouped count query for the bounded parent IDs can supply attachment totals. Use pluck for pure scalar output where model callbacks and associations are unnecessary, but remember that pluck executes immediately and no longer yields a chainable relation. For keyset continuation, apply a lexicographic predicate on created_at and ID matching the descending sort, with an index supporting the filter and order. If the product needs exact numbered pages, choose offset and count deliberately and measure their deep-page cost.",
        cost="A bounded parent page uses O(page width) case memory; preloading one district relation adds a bounded number of district objects. Eager loading a many-valued attachment relation can consume O(total children), and one unusually large permit can dominate that cost. A count query adds database work but transfers far less data than every child record. Deep offset can still scan or skip many rows to return 47; a matching keyset predicate often makes continuation cheaper, although it does not supply a cheap exact page number or stable total during concurrent inserts. Measure SQL count, rows read, bytes returned, object allocations, p95 latency, and database plans on realistic distributions rather than the empty development database.",
        failure="Seed 47 permits with repeated created_at values and follow every cursor page without duplicate or missing IDs. Give one permit 620 attachments and prove the queue reads only its count. Temporarily remove district preload and inspect the extra association queries. Send a cursor produced for reviewer 47 while authenticated as reviewer 81; the next query must still use reviewer 81's assignment scope and cannot reveal reviewer 47's cases. Compare an offset deep in a large fixture with the matching keyset query plan. Alter the template to read an unpreloaded association and make a strict-loading test catch it. Keep a case with no district where the schema allows it and decide whether that row should be omitted or represented as missing.",
        drill="Build a Rails reviewer queue containing permit title, district label, attachment count, and status. Begin with an instrumented 47-row fixture, then add one attachment-heavy permit and timestamp ties. Scope by reviewer assignment and make the order created_at descending with ID as tie breaker. Preload only the district, calculate counts without hydrating attachment models, and project a response hash. Implement next-page continuation with the same SQL permission predicate. Compare number of queries and object allocations before and after the change. Record the index and query plan on the database chosen for the real service. State whether the interface needs numbered navigation or only next-page continuation.",
        decision="Constrain permission and page width in SQL, then optimize the exact relation data the response displays.",
        code='''reviewer_cases = PermitCase.joins(:reviewer_assignments)
  .where(reviewer_assignments: { reviewer_id: reviewer.id })
  .includes(:district)
  .order(created_at: :desc, id: :desc)
  .limit(47)

cards = reviewer_cases.map do |permit|
  { case_id: permit.id, title: permit.title, district: permit.district.name }
end''',
        checks=["The reviewer predicate remains in SQL for each page.", "District reads do not create one query per permit.", "Attachment objects are not loaded merely to display a count."],
        mistakes=["Fixing N+1 by eagerly loading every child association.", "Paginating after Ruby-side filtering.", "Using only a nonunique timestamp as cursor order."],
        related=["web-tech/data-persistence", "web-tech/laravel-eloquent-loading-and-cursor-page-cost", "web-tech/flask-sqlalchemy-session-and-query-lifetime"],
    ),
    dict(
        slug="rails-locking-transaction-and-command-replay",
        title="Rails Locking, Transaction, and Command Replay",
        summary="Lock current case state, commit one approval result, and recover a lost response by operation ID.",
        concept="An approval is a state transition with a durable outcome, not a field assignment from submitted params. Rails validation can reject an invalid model state, while a transaction makes the case change, audit operation, and outbox intent one unit. Row locking or another concurrency rule is needed when two reviewers can race on the same case. A request can commit and still lose its HTTP response. A stable operation ID, command digest, and unique database constraint let the caller replay that logical command and recover the stored result. The same key with changed content must be a conflict. Model callbacks may run during save, but an external provider call inside a retried transaction cannot be rolled back with the database.",
        case="Reviewer 47 approves case 62 while reviewer 81 loses assignment to it. Two requests arrive close together; one comes from a browser retry after a dropped response. If the controller calls update!(status: 'approved') directly, it can create duplicate audit rows and ignore the assignment change. A callback sends an email before commit, then a later validation raises and the database rolls back, leaving a false notice. The repaired service checks the existing operation key first, locks the current case row, verifies revision and assignment again, and commits one case transition, operation result, and outbox row. A repeated exact request reads the stored outcome; a different command under that key is rejected.",
        implementation="Define an operation ID namespace and enforce its uniqueness in the database, not a process-local cache. Parse the revision and reason strictly at the controller boundary. Inside a short transaction, lock the case where the chosen database supports row locks, then check reviewer assignment, legal transition, and expected revision against current state. Insert the operation record and outbox event in the same transaction as the status update. If a duplicate key race occurs, reload the winner's operation and compare its command digest before returning its saved public result. Do not swallow serialization or deadlock errors with a partial response; retry the whole transaction only for the database's explicitly retryable errors, with a bounded attempt budget and no external side effects inside the closure.",
        cost="A row lock serializes conflicting approvals on case 62 and may increase wait time for a hot queue. Keeping the transaction short reduces lock duration. A unique index on operation identity adds write and storage cost but arbitrates across all application processes. Retaining operation results for the promised retry horizon uses space and needs a deletion policy that will not make late legitimate retries execute twice. The outbox adds one write and later scan work. A whole-transaction retry can multiply database work under contention, so record lock wait, retry count, duplicate-key incidence, and p95 command latency. Returning a stored replay outcome can be cheaper than repeating mutation work, but only after the payload identity is checked.",
        failure="Post a stale revision, an invalid reason, a case with no current assignment, and an already-approved case; each must have a distinct deliberate result with no extra audit event. Race two exact requests under one operation ID from separate connections, then assert one status transition and one outbox row. Drop the successful HTTP response and replay the exact command. Reuse the ID with a different reason and require a conflict. Raise after case update but before outbox insertion and confirm rollback removes every change. Simulate a database deadlock and verify any retry reruns the entire transaction, not only the last statement. Record whether SQLite test behavior differs from the production database's row-lock semantics.",
        drill="Implement ApprovePermit as a service object with reviewer ID, case ID, operation ID, expected revision, and reason. Seed case 62 in review at revision 5. Add a unique operation identity, command digest, stored public outcome, and notification outbox table. Use a short transaction and current-state lock; write the case, operation, and event together. Exercise simultaneous same-key calls, two different keys competing for the same revision, a lost response, changed-payload replay, and a rollback after status update. Keep the controller responsible for request parsing and response mapping. Measure lock waits and inspect the final database rows rather than judging correctness from HTTP status alone.",
        decision="Make current-state permission and one logical command outcome database facts, then let retries recover them.",
        code='''require "digest"
require "json"

class ApprovePermit
  def self.call(reviewer:, case_id:, operation_id:, expected_revision:, reason:)
    fingerprint = Digest::SHA256.hexdigest(JSON.generate([case_id, expected_revision, reason]))
    PermitCase.transaction do
      permit = PermitCase.lock.find(case_id)
      prior = ApprovalOperation.find_by(case_id: case_id, operation_id: operation_id)
      if prior
        raise OperationConflict unless prior.reviewer_id == reviewer.id && prior.command_digest == fingerprint
        prior
      else
        raise NotAuthorized unless permit.reviewer_assignments.exists?(reviewer_id: reviewer.id)
        raise StaleRevision unless permit.revision == expected_revision

        permit.update!(status: "approved", revision: permit.revision + 1)
        operation = ApprovalOperation.create!(
          operation_id: operation_id, case_id: case_id, reviewer_id: reviewer.id,
          command_digest: fingerprint, reason: reason, result_status: permit.status
        )
        ApprovalOutbox.create!(approval_operation_id: operation.id, state: "pending")
        operation
      end
    end
  end
end''',
        checks=["Permission and revision are checked against locked current state.", "Case, operation, and outbox rows share one transaction.", "A uniqueness constraint resolves concurrent replay across processes."],
        mistakes=["Passing status from strong params directly into update!.", "Using only a controller-side existence check for replay.", "Sending email from a retried transaction or save callback."],
        related=["web-tech/api-mutation-and-failure-contracts", "web-tech/django-form-csrf-atomic-approval-and-on-commit", "web-tech/laravel-form-request-transaction-and-approval-replay"],
    ),
    dict(
        slug="rails-active-job-after-commit-and-outbox-recovery",
        title="Rails Active Job After-Commit and Outbox Recovery",
        summary="Delay worker visibility until commit and retain intent when the enqueue handoff fails.",
        concept="Active Job schedules work through an adapter, but a queue handoff has its own lifetime. A job queued before the approval transaction commits may run against a case state that is invisible to its connection, or against a transaction that later rolls back. Rails can defer enqueue until after commit, which fixes that ordering problem across queue backends. It does not make the queue request itself a durable part of the case transaction when the adapter uses separate storage. If the process dies after commit and before enqueue, promised work is lost unless the database also contains an outbox row committed with the approval. A worker should receive an event ID, claim the row, and use stable identity for retries.",
        case="Case 62 changes to approved and a notification job is scheduled inside the transaction. On a fast worker, the job reads the previous status; on rollback, a notice may still be queued. Deferring enqueue until commit fixes those races. Then the web process dies just after commit and before it can reach the queue. With no other record, the notice disappears. The repaired service writes outbox event 93 with the case change. After commit, an Active Job wake-up can accelerate delivery. A separate sweep finds pending event 93 even when that wake-up was lost. The worker claims it under a lease, sends with a stable provider key where possible, and records delivered or review-needed state.",
        implementation="Configure after-transaction enqueue behavior for the job or schedule it from a post-commit boundary, and verify the setting under the deployed Rails version and adapter. Treat that enqueue as a hint, not the only record of intent. Write the outbox event inside the same database transaction as the approved case and operation result. Give workers a narrow event ID instead of serializing an Active Record object whose state and permission may change. A claim must be atomic across workers; use a lease or row transition with expiry, finite retries, and an inspectable permanent-failure state. A scheduled sweep should scan a bounded number of pending rows and release expired claims. Recheck recipient policy if it can change before delivery.",
        cost="An outbox event adds a write and retention cost, while a sweep and worker pool add reads and operational capacity. Deferring enqueue can add a brief delay but prevents the worker from seeing uncommitted state. A database-backed queue in the same database may have different atomicity from a queue on another database or broker; the architecture should not rely on an accidental shared-transaction setup. Provider timeouts are ambiguous because a send may have succeeded before acknowledgment was lost. A stable event key or provider reconciliation narrows duplicate delivery but does not create a universal exactly-once guarantee. Measure oldest pending event age, queue lag, lease expiry, attempt count, provider outcomes, and permanent failures.",
        failure="Roll back approval and verify there is neither a committed outbox event nor a worker-visible job for it. Commit approval and kill the web process before enqueue; restart the sweep and confirm event 93 is found. Run two workers against the same event and require a single active lease. Crash after claim, let the lease expire, and verify another worker can recover. Make the provider accept the notification but drop its acknowledgment; retry under the same event key and inspect whether the provider deduplicates or whether reconciliation is needed. Stop all workers and watch the oldest pending age rise. Force a permanent invalid recipient and confirm the event reaches an operator-visible state instead of retrying forever.",
        drill="Create a Rails notification outbox for permit approvals. Configure the wake-up job to enqueue after commit and pass only the outbox row ID. Have a sweep inspect at most 47 pending rows per pass; each worker must atomically claim a row, use a bounded attempt policy, and persist delivered or review-needed status. Inject failures before commit, after commit but before enqueue, during provider send, and after provider acceptance but before worker acknowledgment. Record the event's stable external key and the result of every attempt without copying private case fields into queue payloads. Verify behavior under the production queue adapter and its actual database topology.",
        decision="Use after-commit enqueue for ordering and a transactional outbox for recoverable delivery intent.",
        code='''class PermitOutboxWakeJob < ApplicationJob
  self.enqueue_after_transaction_commit = true
  queue_as :notifications

  def perform(event_id)
    event = ApprovalOutbox.find_by(id: event_id)
    return unless event&.pending?

    PermitNotificationDispatcher.claim_and_deliver(event.id)
  end
end

ApprovalOutbox.pending.order(:id).limit(47).pluck(:id).each do |event_id|
  PermitOutboxWakeJob.perform_later(event_id)
end''',
        checks=["The outbox row commits with the approved case.", "The wake-up job runs only after commit and receives an ID.", "A sweep finds pending events even when enqueue was lost."],
        mistakes=["Assuming after-commit enqueue makes a separate queue write atomic with the case transaction.", "Sending a stale model snapshot as the job payload.", "Retrying provider timeouts with a new unrelated identity."],
        related=["web-tech/background-workflow-reliability", "web-tech/laravel-after-commit-jobs-and-outbox-recovery", "web-tech/flask-async-views-and-durable-background-work"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/fastapi-contract-and-resource-boundaries"])
hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)), path=hub_path, title=hub_title,
           summary="Build Rails permit services with scoped controllers, bounded Active Record reads, replay-safe transactions, and recoverable jobs.",
           sort_order=3750, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    subprocess.run(["ruby", "-c"], input=topic["code"], text=True, check=True, capture_output=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=topic["title"], summary=topic["summary"], sort_order=3751 + number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-ruby">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
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
hub["body"] = paragraph("A Rails permit request crosses four distinct boundaries: the controller admits and scopes a reviewer, Active Record shapes a bounded queue, a short transaction commits one approval, and Active Job moves notification work beyond the response. Follow case 62 through each boundary. Every lesson traces a failure that can survive a passing happy-path request test, then asks for measurements and recovery evidence.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/backend-api-systems", "web-tech/authorization-and-tenant-boundaries", "web-tech/data-persistence"]) + ".</p>"
curriculum = by_path["web-tech/web-technology"]
curriculum["data"]["modules"].append({"title": hub_title, "summary": hub["summary"],
                                       "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
curriculum["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
curriculum["updated_at"] = stamp
crosslinks = {
    "web-tech/backend-api-systems": [hub_path],
    "web-tech/authorization-and-tenant-boundaries": ["web-tech/rails-controller-parameters-and-object-permission"],
    "web-tech/data-persistence": ["web-tech/rails-active-record-scope-eager-load-and-page-cost"],
    "web-tech/api-mutation-and-failure-contracts": ["web-tech/rails-locking-transaction-and-command-replay"],
    "web-tech/background-workflow-reliability": ["web-tech/rails-active-job-after-commit-and-outbox-recovery"],
    "web-tech/laravel-policy-query-and-queue-boundaries": [hub_path],
    "web-tech/flask-context-and-service-boundaries": [hub_path],
}
for path, targets in crosslinks.items():
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4,
                  "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))

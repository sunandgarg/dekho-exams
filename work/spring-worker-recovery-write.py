"""Add original, source-backed Spring worker and outbox recovery lessons."""
from __future__ import annotations

import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
specs = []


def add(subject, slug, title, definition, sections, code, proof, limits, mistakes, related):
    specs.append(dict(subject=subject, path="spring/" + slug, slug=slug,
        title=title, definition=definition, sections=sections, code=code,
        proof=proof, limits=limits, mistakes=mistakes, related=related))


add("spring-core", "bounded-executor-rejection", "Spring task executors: reject work when every slot is occupied",
"A bounded ThreadPoolTaskExecutor can reject a new task when its worker and queue are both occupied.", [
    ("Make saturation observable", ["The source-kit fixture configures one worker, one waiting slot and the default rejection policy. The first receipt dispatch blocks behind a test latch; the second waits in the queue. A third submission throws TaskRejectedException. After release, both accepted tasks finish. That is a check of admission, not delivery.", "Spring queues work after core threads are occupied and grows beyond the core size only after a finite queue fills. With a fixed one-thread pool there is no extra worker to create. An unbounded queue can make a configured maximum pool size irrelevant and move overload into memory. The related [[spring/async-future-failure|future lesson]] covers errors after admission; this lesson covers a failure at submission."]),
    ("Map rejection to a real contract", ["A request handler that catches rejection must say whether it persisted a command before returning. If the command exists in an [[spring/outbox-atomic-write|outbox]], the worker can retry later. If it only existed as an in-memory Runnable, a successful HTTP acceptance claim would be false. Do not silently switch to CallerRunsPolicy unless the request thread is allowed to execute potentially slow work and its deadline accounts for that cost."])
], '''executor.setCorePoolSize(1);
executor.setMaxPoolSize(1);
executor.setQueueCapacity(1);
executor.initialize();
Future<?> first = executor.submit(blockedReceiptDispatch);
Future<?> second = executor.submit(queuedReceiptDispatch);
assertThrows(TaskRejectedException.class,
    () -> executor.submit(overflowReceiptDispatch));''',
"BoundedExecutorContractTest.thirdTaskIsRejectedWhileOneRunsAndOneWaits",
"This local test checks one configuration and one saturated instant. Queue memory is O(capacity), plus task-held objects. It does not measure throughput, fairness, shutdown drain, HTTP status mapping or behavior under several application replicas.",
["Do not use an unbounded queue when admission must have a limit.", "Do not report accepted work after an executor rejected it.", "Do not treat an executor queue as restart-safe storage."],
["spring/async-future-failure", "spring/async-vs-durable-delivery", "spring/outbox-atomic-write"])

add("spring-core", "async-admission-and-completion", "Spring async work has two failure points: submission and completion",
"An asynchronous command may fail before a worker accepts it or after the worker starts it.", [
    ("Observe both edges", ["The bounded executor fixture throws TaskRejectedException on its third submission. A separate managed @Async service returns a failed CompletableFuture whose cause is visible when the caller joins it. These are different failures. A retry on completion is impossible if the caller threw away its future; a retry on submission must not claim that the task was queued.", "If HTTP returns before completion, name the response honestly. Durable acceptance requires a committed record such as [[spring/outbox-atomic-write|an outbox row]]. In-memory acceptance provides only a process-local promise. A receipt ID and a queryable state can bridge that gap, but the state transition and worker must be implemented rather than inferred from @Async. [[spring/bounded-executor-rejection|The saturation fixture]] tests capacity one."]),
    ("Keep ownership at the boundary", ["Give the caller or worker a timeout, a cancellation rule and a place to record terminal failure. Cancellation is not proof that a remote side effect did not occur. If the worker sends a message and fails before marking it done, a later replay can send it again. Design the [[spring/consumer-dedup-transaction|consumer's duplicate rule]] before calling the delivery path reliable."])
], '''try {
    Future<?> accepted = dispatchExecutor.submit(receiptDispatch);
    accepted.get(5, TimeUnit.SECONDS);
} catch (TaskRejectedException full) {
    // Nothing entered this executor queue.
} catch (ExecutionException failed) {
    // The accepted worker failed after submission.
}''',
"BoundedExecutorContractTest.thirdTaskIsRejectedWhileOneRunsAndOneWaits and AsyncFailureContractTest.failureIsObservedThroughTheReturnedFuture",
"The excerpts combine two separate local tests. They do not implement one end-to-end dispatcher, a durable queue, a configured production executor or a network timeout. Completion state consumes memory until its owner releases the future.",
["Do not merge submission rejection with worker failure in one vague error state.", "Do not discard an important future.", "Do not infer durable acceptance from a successful submit call."],
["spring/bounded-executor-rejection", "spring/async-future-failure", "spring/consumer-dedup-transaction"])

add("spring-data", "outbox-expiring-lease", "Spring outbox claims: allow recovery after a worker lease expires",
"An expiring outbox lease lets another worker reclaim a pending event after the current worker stops making progress.", [
    ("Claim with one conditional write", ["The H2 fixture writes an event E-41, then lets worker-A claim it until logical time 200. Worker-B cannot claim at time 150. At 200 it can replace the expired token. The SQL update checks state and lease time in the same statement, so the returned row count tells the caller whether it owns the row in this fixture. [[spring/outbox-claim-state|The earlier claim-state lesson]] checks a simple pending-to-claimed transition without expiry.", "Use a database clock or an agreed clock policy in a real service. The fixture passes deterministic long values so the boundary is testable. It does not prove behavior under clock skew, a long network pause, database lock contention or a two-node race. Keep the claim transaction short; do not hold a row lock while calling a broker."]),
    ("An expiry is not a cancellation", ["Worker-A may still be sending after its lease expires. Its send can race worker-B's retry. A lease permits recovery; it does not enforce exactly-once external delivery. [[spring/outbox-fenced-ack|A token-checked acknowledgement]] stops an old worker from marking the new owner's row done, and [[spring/consumer-dedup-transaction|a consumer ledger]] handles repeated event IDs at the destination."])
], '''update delivery_outbox
set claim_token = ?, lease_until = ?
where event_id = ? and delivered = false
  and (claim_token is null or lease_until <= ?);''',
"OutboxLeaseContractTest.expiredLeaseCanBeReclaimedButOldWorkerCannotAcknowledge",
"The check uses one row and sequential statements on H2. Each scan or update costs database I/O; an index and target-database query plan are needed for a large pending set. The test does not establish concurrent fairness, crash recovery across processes or broker delivery.",
["Do not interpret lease expiry as proof the former worker has stopped.", "Do not hold a database transaction open during network delivery.", "Do not assume test-supplied timestamps cover production clock behavior."],
["spring/outbox-claim-state", "spring/outbox-fenced-ack", "spring/consumer-dedup-transaction"])

add("spring-data", "outbox-fenced-ack", "Outbox acknowledgements: require the current lease token",
"An outbox acknowledgement should update a row only when the caller still holds its current claim token.", [
    ("A stale owner must lose", ["Worker-A claims E-41. After the logical lease expires, worker-B reclaims it. An acknowledgement carrying worker-A's token updates zero rows; worker-B's token marks the row delivered. The fixture also checks that a delivered row cannot be claimed again. Counting affected rows makes a lost lease visible instead of treating every acknowledgement as success.", "The token belongs in the update predicate with the event ID and incomplete state. A plain update by event ID lets a slow former worker mark another owner's attempt complete. [[spring/outbox-expiring-lease|The lease lesson]] shows how the owner changes. A unique token should be generated per claim attempt, not reused as a permanent worker name in production; this fixture's readable names are only deterministic test markers."]),
    ("Fencing protects the row, not the destination", ["The old worker could already have sent an event before its stale acknowledgement failed. The token prevents a stale database state transition but cannot retract an external message. Keep the event ID stable across retries and make the [[spring/consumer-dedup-transaction|destination mutation idempotent]]. Also record failed acknowledgement attempts so an operational view can distinguish a lease loss from a database outage."])
], '''update delivery_outbox
set delivered = true
where event_id = ? and claim_token = ? and delivered = false;''',
"OutboxLeaseContractTest.expiredLeaseCanBeReclaimedButOldWorkerCannotAcknowledge",
"This H2 row-count test proves a conditional state transition in one database. It does not include token generation, concurrent worker scheduling, send acknowledgements, broker retries or dead-letter handling. Each acknowledgement is one indexed row update when event_id is a primary key.",
["Do not acknowledge by event ID alone after introducing leases.", "Do not reuse a token across distinct claim attempts.", "Do not call a fenced row update exactly-once message delivery."],
["spring/outbox-expiring-lease", "spring/consumer-dedup-transaction", "spring/outbox-atomic-write"])

add("spring-data", "consumer-dedup-transaction", "Spring consumer deduplication: commit the event ID with the mutation",
"A consumer can make repeated delivery harmless by recording an event ID and its business mutation in one database transaction.", [
    ("The key and stock change share one commit", ["The source-kit fixture starts with 10 units for SKU-41. Event E-41 adds four; a repeated E-41 hits the primary key on applied_event and the stock stays at 14. A different E-42 removes two, leaving 12. Spring's TransactionTemplate groups the ledger insert and stock update; the duplicate exception is observed outside that transaction. This checks local database effects, not broker acknowledgement.", "Place the event key in a uniqueness constraint rather than only checking a map or doing a read-before-write. Under concurrent consumers, a separate read can see no row twice; the database constraint decides which insert wins. A production handler should classify a true duplicate and acknowledge it without repeating the mutation, while treating an event ID reused with different payload as a conflict. The fixture rejects both by key and does not compare payload hashes."]),
    ("Know the remaining gap", ["If the database commits and the message acknowledgement fails, the broker may redeliver. The ledger makes that repeat a no-op for this database state. If the handler also sends mail, calls another service or publishes outside the transaction, those effects need their own idempotency keys. Pair this with [[spring/outbox-fenced-ack|fenced outbox acknowledgement]] at the sender and [[spring/outbox-atomic-write|atomic outbox write]] at its origin."])
], '''transaction.executeWithoutResult(status -> {
    jdbc.update("insert into applied_event (event_id) values (?)", eventId);
    jdbc.update("update stock_balance set available = available + ? where sku = ?",
        units, "SKU-41");
});''',
"ConsumerDedupContractTest.repeatedEventIdCannotApplyTheStockMutationTwice",
"Two small H2 tables check one duplicate and one distinct event. A primary-key probe adds write and index cost; retained IDs consume storage and need an expiry policy tied to the broker's maximum redelivery window. This fixture does not test multiple consumers, payload mismatch classification, nonnegative inventory or remote side effects.",
["Do not check for an ID and then write without a database uniqueness constraint.", "Do not record the ID in a different transaction from the business change.", "Do not treat duplicate suppression as proof that all external effects are idempotent."],
["spring/outbox-atomic-write", "spring/outbox-fenced-ack", "spring/idempotent-receipt-post"])

add("spring-production", "at-least-once-delivery-boundary", "At-least-once delivery: where Spring outbox retries can duplicate work",
"An outbox relay can send the same event more than once when sending succeeds but its acknowledgement does not persist.", [
    ("The crash window is real", ["The source kit checks three separate boundaries: business and outbox rows commit together, a lease can be reclaimed with a new token, and a repeated event ID does not apply the local stock mutation twice. None of those tests includes a broker. Together they define a useful recovery contract: a stable event ID survives retries, the current lease owner may update outbox state, and the destination records the ID with its mutation.", "A broker send followed by a database update cannot normally be one ordinary local transaction. A worker might stop between them. Retrying the row then repeats the send. [[spring/outbox-fenced-ack|Fencing]] blocks a stale row update; [[spring/consumer-dedup-transaction|deduplication]] blocks a repeated destination mutation. Neither can promise an email or payment provider executed only once without that provider's own idempotency rule."]),
    ("Operational states still matter", ["Track pending, leased, delivered and terminal failure separately. Put a bound on attempts and record the last error without copying secrets into logs. Alert on the oldest pending age rather than only queue size; one stuck event can disappear in a large healthy queue. Before launch, test service restart after database commit, after send, and before acknowledgement against the actual broker and database. The local fixture does not cover those failures."])
], '''// Recovery state, expressed as two checked row predicates:
claim: delivered = false AND (claim_token IS NULL OR lease_until <= now)
ack: event_id = ? AND claim_token = ? AND delivered = false''',
"OutboxWriteContractTest.receiptAndOutboxRowCommitOrRollBackTogether, OutboxLeaseContractTest.expiredLeaseCanBeReclaimedButOldWorkerCannotAcknowledge and ConsumerDedupContractTest.repeatedEventIdCannotApplyTheStockMutationTwice",
"The three tests run on H2 in one process and are independent. They establish row outcomes, not end-to-end delivery, throughput, broker ordering or restart recovery. A relay adds scan, lock, network and retry costs that depend on deployment and batch size.",
["Do not call an outbox exactly-once delivery.", "Do not discard the event ID on retry.", "Do not assume successful send implies a persisted acknowledgement."],
["spring/outbox-atomic-write", "spring/outbox-expiring-lease", "spring/consumer-dedup-transaction"])

add("spring-testing", "worker-recovery-test-matrix", "Test a Spring worker at admission, lease and replay boundaries",
"Worker recovery tests should assert the state left behind at each failure point, not just that an exception occurred.", [
    ("Three local observations", ["The bounded executor test fills one running and one waiting slot, then sees a rejected third task. The outbox test checks claim refusal before expiry, takeover at expiry and a zero-row stale acknowledgement. The consumer test verifies that a repeated event ID does not alter the stock again. Each assertion examines the state the next worker would encounter.", "These are separate fixtures, not an end-to-end worker. They do not share one HTTP handler, broker or database. The [[spring/failure-layer-matrix|layer matrix]] explains why a small local check cannot prove a deployment property. A useful integration test would stop a relay after commit, restart it, deliver the same event twice and inspect destination state and acknowledgement history."]),
    ("Inject failure at every handoff", ["A larger suite should fail between receipt commit and claim, after claim but before send, after send but before acknowledgement, and after destination commit but before broker ack. Use a target database and actual broker test environment before making guarantees about lock behavior or redelivery. Record the maximum delay and retry count expected by the product. Without those values, a green unit suite can still conceal a user-visible stuck receipt."])
], '''assertThrows(TaskRejectedException.class,
    () -> executor.submit(overflowReceiptDispatch));
assertEquals(0, acknowledge(jdbc, "E-41", "stale-token"));
assertThrows(DuplicateKeyException.class,
    () -> apply(jdbc, transaction, "E-41", 4));''',
"BoundedExecutorContractTest.thirdTaskIsRejectedWhileOneRunsAndOneWaits, OutboxLeaseContractTest.expiredLeaseCanBeReclaimedButOldWorkerCannotAcknowledge and ConsumerDedupContractTest.repeatedEventIdCannotApplyTheStockMutationTwice",
"The three assertions come from independent local tests and are condensed here. The kit has no crash injector, broker or target database. Those tests are needed to measure recovery time and verify behavior across process boundaries.",
["Do not mistake three green unit fixtures for one delivery service.", "Do not assert only status codes when the failure is about retained state.", "Do not omit a test for the send-before-acknowledgement gap."],
["spring/bounded-executor-rejection", "spring/outbox-expiring-lease", "spring/consumer-dedup-transaction"])

add("spring-projects", "receipt-delivery-recovery-plan", "Spring Boot receipt delivery project: add a recoverable worker contract",
"A recoverable receipt delivery service needs one durable command record, an owned outbox claim and a duplicate-safe destination mutation.", [
    ("Build from checked pieces", ["The existing [[spring/receipt-delivery-project|receipt delivery project]] is a plan, not a deployed service. The kit separately checks an atomic receipt/outbox insert, a token and expiry predicate, and a destination event-ID ledger. A practical next implementation would place the receipt API and outbox write in one service transaction, then run a relay that claims a bounded batch, sends stable event IDs, and acknowledges only with its current claim token.", "The destination inserts the event ID and applies its business change in one transaction. If it sees the same ID again, it must classify the replay and avoid a second change. The local duplicate test currently throws; an API or broker adapter still needs to turn that into a safe acknowledgement. For a changed payload under the same ID, reject and investigate rather than pretending the new event was processed."]),
    ("Prove recovery before exposure", ["Keep worker concurrency, batch size, lease duration and retry cap configurable and measured. Test process termination after each handoff against the chosen database and broker. The target connection pool must cover request and worker load; the ready probe should reflect dependencies the service cannot operate without. None of those deployment properties is established by the local kit. [[spring/worker-recovery-test-matrix|The test matrix]] names the missing failure points."])
], '''// One public receipt request produces one durable event ID.
receiptTransaction.executeWithoutResult(status -> {
    receiptRepository.insert(receiptId, tenantId, "accepted");
    outboxRepository.insert(eventId, receiptId, "pending");
});
// A separate relay claims, sends, and acknowledges with its current token.''',
"OutboxWriteContractTest.receiptAndOutboxRowCommitOrRollBackTogether, OutboxLeaseContractTest.expiredLeaseCanBeReclaimedButOldWorkerCannotAcknowledge and ConsumerDedupContractTest.repeatedEventIdCannotApplyTheStockMutationTwice",
"This is an implementation plan grounded in separate checked fixtures, not a runnable combined application. A real service adds migrations, broker I/O, pool sizing, observability, tenant authorization and operations under load. The current API uses an in-memory store.",
["Do not label the project deployed because its component tests pass.", "Do not return durable acceptance before the command transaction commits.", "Do not turn a duplicate event into a second business mutation."],
["spring/receipt-delivery-project", "spring/outbox-atomic-write", "spring/outbox-expiring-lease", "spring/consumer-dedup-transaction"])


def para(value: str) -> str:
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda found: '<a href="/' + found[1] + '">' + found[2] + "</a>", escaped) + "</p>"


titles = {path: row["title"] for path, row in by_path.items()}
titles.update({spec["path"]: spec["title"] for spec in specs})
for spec in specs:
    path = spec["path"]
    assert path not in by_path, path
    assert all(target in titles for target in spec["related"]), (path, spec["related"])
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == spec["subject"])
    body = para(spec["definition"])
    for heading, paragraphs in spec["sections"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(para(value) for value in paragraphs)
    language = "sql" if path in {"spring/outbox-expiring-lease", "spring/outbox-fenced-ack"} else "text" if path == "spring/at-least-once-delivery-boundary" else "java"
    body += '<h2>Checked source</h2><pre><code class="language-' + language + '">' + html.escape(spec["code"].strip(), quote=False) + "</code></pre>"
    body += "<h2>Verification boundary</h2>" + para(spec["proof"] + " runs in the downloadable Spring source kit. The excerpt is shortened; the kit contains the complete tests.")
    body += "<h2>Costs and limits</h2>" + para(spec["limits"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2>" + para(", ".join("[[" + target + "|" + titles[target] + "]]" for target in spec["related"]) + ".")
    row = by_path["spring/if-match-receipt-write"].copy()
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), type="article",
        path=path, title=spec["title"], summary=spec["definition"], body=body,
        subject=spec["subject"], difficulty="Intermediate", status="published",
        tags=["spring", "spring-boot", spec["slug"]], featured=False,
        sort_order=900 + len(rows), published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot", "section_path": hub["path"],
        "kind": "tutorial", "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "seo_ready": True,
        "related": [{"path": target, "title": titles[target]} for target in spec["related"]],
        "framework_version": "Spring Boot 4.0.8 / Spring Framework 7",
        "java_version": "21 source-kit baseline", "verification_suite": spec["proof"],
        "download_path": "/downloads/aitrove-spring-source-kit.zip"}
    rows.append(row)
    by_path[path] = row

grouped = {
    "spring-core": ("Bounded async admission", ["spring/bounded-executor-rejection", "spring/async-admission-and-completion"]),
    "spring-data": ("Outbox leases and duplicate-safe consumers", ["spring/outbox-expiring-lease", "spring/outbox-fenced-ack", "spring/consumer-dedup-transaction"]),
    "spring-production": ("Delivery recovery boundaries", ["spring/at-least-once-delivery-boundary"]),
    "spring-testing": ("Worker recovery checks", ["spring/worker-recovery-test-matrix"]),
    "spring-projects": ("Recoverable receipt delivery", ["spring/receipt-delivery-recovery-plan"]),
}
for subject, (title, paths) in grouped.items():
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    hub["data"]["modules"].append({"title": title,
        "summary": "Run the local fixture and inspect the retained state.", "lessons": paths})
    hub["updated_at"] = stamp
    if "<h2>Section lessons</h2>" in hub["body"]:
        links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
            for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)",
            lambda found: found[1] + links + found[2], hub["body"])

reverse = {
    "spring/async-boundaries": ["spring/bounded-executor-rejection", "spring/async-admission-and-completion"],
    "spring/async-vs-durable-delivery": ["spring/bounded-executor-rejection"],
    "spring/outbox-atomic-write": ["spring/outbox-expiring-lease", "spring/consumer-dedup-transaction"],
    "spring/outbox-claim-state": ["spring/outbox-expiring-lease", "spring/outbox-fenced-ack"],
    "spring/testing-boundaries": ["spring/worker-recovery-test-matrix"],
    "spring/receipt-delivery-project": ["spring/receipt-delivery-recovery-plan"],
    "spring/actuator-health": ["spring/at-least-once-delivery-boundary"],
    "java/completable-future": ["spring/async-admission-and-completion"],
    "java/jdbc-transactions": ["spring/consumer-dedup-transaction"],
}
for path, targets in reverse.items():
    assert path in by_path, path
    row = by_path[path]
    marker = "<h2>Continue with checked worker recovery</h2>"
    row["body"] = row["body"].split(marker)[0] + marker + para("Continue with " + ", ".join(
        "[[" + target + "|" + titles[target] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [spec["path"] for spec in specs], "count": len(specs)}))

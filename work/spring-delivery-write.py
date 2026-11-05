"""Add source-backed Spring delivery, HTTP, security and operations lessons."""
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
added = []


def para(value: str) -> str:
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>", escaped) + "</p>"


def lesson(subject, slug, title, definition, sections, source, proof, cost, mistakes, related):
    path = "spring/" + slug
    assert path not in by_path, path
    assert all(target in by_path for target in related), (path, related)
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    body = para(definition)
    for heading, paragraphs in sections:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(para(value) for value in paragraphs)
    body += '<h2>Checked source</h2><pre><code class="language-java">' + html.escape(source.strip(), quote=False) + "</code></pre>"
    body += "<h2>Verification boundary</h2>" + para(proof + " runs in the downloadable Spring source kit. The excerpt leaves out surrounding setup and imports; the kit contains the complete test.")
    body += "<h2>Costs and limits</h2>" + para(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + para(", ".join("[[" + target + "|" + by_path[target]["title"] + "]]" for target in related) + ".")
    row = by_path["spring/if-match-receipt-write"].copy()
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), type="article",
        path=path, title=title, summary=definition, body=body, subject=subject,
        difficulty="Intermediate", tags=["spring", "spring-boot", slug], status="published",
        featured=False, sort_order=850 + len(added),
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot", "section_path": hub["path"],
        "kind": "tutorial", "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "seo_ready": True,
        "related": [{"path": target, "title": by_path[target]["title"]} for target in related],
        "framework_version": "Spring Boot 4.0.8 / Spring Framework 7",
        "java_version": "21 source-kit baseline", "verification_suite": proof,
        "download_path": "/downloads/aitrove-spring-source-kit.zip"}
    rows.append(row)
    by_path[path] = row
    added.append(path)


lesson("spring-data", "outbox-atomic-write", "Spring transactional outbox: commit a receipt and event row together",
"A transactional outbox stores the business change and a pending delivery record in one database transaction.", [
    ("One commit boundary", ["The checked H2 fixture inserts receipt R-41 and outbox event E-41 through one Spring TransactionTemplate. A failure before commit leaves neither row. A successful retry leaves one of each. The event row is a promise to attempt delivery later, not evidence that a broker has received anything.", "A direct broker call inside the transaction cannot be rolled back with the database. Sending only after commit avoids that ordering problem but can still lose a message if the process exits before sending. The stored event closes that particular gap when a worker later scans it. [[spring/transaction-events|After-commit listeners]] alone do not make delivery durable."]),
    ("The database boundary still needs a schema", ["Give the event its own stable ID, a state, and enough payload or a reference to reconstruct the delivery. Insert both rows with the same DataSource and transaction manager. A second database, external queue or independent transaction breaks the atomic claim. [[spring/outbox-claim-state|Claiming pending rows]] is the next boundary, not part of this commit."])
], '''transaction.executeWithoutResult(status -> {
    jdbc.update("insert into receipt values (?, ?)", "R-41", "accepted");
    jdbc.update("insert into outbox values (?, ?, ?)", "E-41", "R-41", "pending");
});''', "OutboxWriteContractTest.receiptAndOutboxRowCommitOrRollBackTogether",
"Two indexed inserts are O(log n) in the usual B-tree model, plus commit and log I/O; that is not a latency promise. The local H2 test proves rollback and commit together for one transaction manager. It does not test broker delivery, crash recovery, production isolation or schema migration.",
["Do not call an after-commit callback a durable queue.", "Do not write the business row and event row through unrelated transactions.", "Do not mark an event delivered when only the database commit succeeded."],
["spring/transactions", "spring/transaction-events", "spring/transaction-propagation"])

lesson("spring-data", "outbox-claim-state", "Spring outbox claims: move pending work once per database state",
"An outbox claim changes a pending record to claimed only if it is still pending, so a second claimant can observe that it lost the state transition.", [
    ("Use the affected-row count", ["The H2 fixture changes E-41 from pending to claimed with a guarded UPDATE. The first call changes one row; repeating it changes zero. Treat zero as a lost claim, not as a successful delivery. The claim belongs after [[spring/outbox-atomic-write|the atomic business write]] and before any external send.", "One UPDATE is a useful local predicate, but a production worker needs a lease or another recovery rule. If a process dies after claiming and before sending, a permanent claimed flag strands the event. If the send succeeds and acknowledgement fails, retry can duplicate delivery. Consumers must tolerate repeated event IDs."]),
    ("Make ownership recoverable", ["A durable design stores a claim token, deadline, attempt count and last failure under a target database transaction. Release or renew only when the token still matches. Do not let an expired worker complete a row owned by a newer worker. The source kit checks the simple state transition only; multi-worker and crash behavior remain untested."])
], '''int claimed = jdbc.update(
    "update outbox set state = 'claimed' where id = ? and state = 'pending'", "E-41");
if (claimed != 1) throw new IllegalStateException("claim lost");''', "OutboxWriteContractTest.receiptAndOutboxRowCommitOrRollBackTogether",
"A primary-key guarded update is usually indexed, but lock waits and database isolation can dominate elapsed time. This lesson verifies one H2 transition, not concurrent worker exclusion, lease expiry or exactly-once delivery.",
["Do not infer exactly-once delivery from one successful UPDATE.", "Do not leave claimed rows without a crash-recovery path.", "Do not let an old worker acknowledge a new owner's claim."],
["spring/outbox-atomic-write", "spring/transaction-propagation", "spring/transaction-events"])

lesson("spring-web", "idempotent-receipt-post", "Spring POST idempotency keys: replay the same receipt result",
"An idempotency key lets an API return the recorded result for a repeated create request instead of creating another receipt.", [
    ("Key and request must agree", ["The checked controller requires a nonblank Idempotency-Key. The first key and body create receipt-1. Sending the same key and body again returns receipt-1. Reusing the key with a different body gets 409; a new key can create receipt-2. The service compares exact request text in this fixture, so even harmless formatting differences count as different requests.", "A real service should scope the key to the authenticated owner and operation, store a canonical request fingerprint and the response in durable storage, and perform the record/create decision atomically. A synchronized HashMap covers one controller instance only. It loses history on restart and cannot coordinate other replicas. [[spring/tenant-receipt-write|Tenant write authorization]] is a separate check."]),
    ("Do not confuse replay with preconditions", ["A retry of a create request asks whether the same operation already happened. [[spring/if-match-receipt-write|If-Match]] asks whether a known resource revision is still current before an update. Both can appear in one API, but they protect different failure paths. A network timeout after a commit is exactly where replaying the stored result matters."])
], '''@PostMapping(path = "/contract/idempotent-receipts", consumes = "text/plain")
synchronized ResponseEntity<String> create(
    @RequestHeader(value = "Idempotency-Key", required = false) String key,
    @RequestBody String request) {
    if (key == null || key.isBlank()) return ResponseEntity.badRequest().build();
    Stored prior = accepted.get(key);
    if (prior != null) {
        if (!prior.request().equals(request)) return ResponseEntity.status(409).build();
        return ResponseEntity.ok(prior.receipt());
    }
    String receipt = "receipt-" + (accepted.size() + 1);
    accepted.put(key, new Stored(request, receipt));
    return ResponseEntity.ok(receipt);
}''', "IdempotentReceiptPostTest.replayReturnsTheOriginalReceiptAndConflictingPayloadIsRejected",
"Map lookup is expected O(1) average time within one JVM, but the synchronized method serializes calls and memory grows with retained keys. The test covers local HTTP mapping and response decisions, not durable atomic creation, expiry, authentication, distributed retries or a payment-grade API.",
["Do not mint another receipt for a retry with the same operation key.", "Do not accept the same key with a different request silently.", "Do not use a global key namespace when two tenants can choose the same key."],
["spring/if-match-receipt-write", "spring/tenant-receipt-authorization", "spring/outbox-atomic-write"])

lesson("spring-web", "idempotency-vs-if-match", "Spring retry and stale-write checks: choose the right HTTP contract",
"An idempotency key identifies a repeated operation; If-Match requires a current representation validator before a state-changing request.", [
    ("The two questions are different", ["POST with key intake-41 and body 42 returns the same receipt on replay in the source kit. PUT with a stale receipt ETag returns 412 and does not overwrite the reviewed state. Neither rule authenticates the caller. A tenant can know an ETag or guess a weak key while lacking permission to update the resource.", "For create requests, define key scope, canonical payload, retention and the response to an in-flight duplicate. For update requests, define whether the API requires a strong ETag and how a client refreshes it after 412. The local fixtures handle one quoted tag and one in-memory idempotency map, not the full protocol grammar or a distributed race."]),
    ("Put the checks in the right order", ["Authenticate and authorize the caller, parse and bound the request, then make the replay or revision decision inside the durable write boundary. If a user is denied, do not reveal another tenant's stored replay response. If the database update and replay record commit separately, a timeout can still create duplicate work. [[spring/outbox-atomic-write|Outbox writes]] cover later event delivery, not HTTP replay by themselves."])
], '''// Both branches are checked by separate source-kit tests.
if (prior != null && !prior.request().equals(request)) return ResponseEntity.status(409).build();
if (!currentTag.equals(expectedTag)) return ResponseEntity.status(412).build();''', "IdempotentReceiptPostTest.replayReturnsTheOriginalReceiptAndConflictingPayloadIsRejected and ReceiptIfMatchWriteTest.staleClientCannotOverwriteTheCurrentRevision",
"The excerpt is a decision sketch, not a combined deployable handler. The two tests prove distinct local cases. They do not prove ordering across a real security filter, database transaction, HTTP proxy or concurrent replicas.",
["Do not treat an ETag as an authorization token.", "Do not use If-Match as a substitute for create-request replay storage.", "Do not return another tenant's recorded response based only on a matching key."],
["spring/idempotent-receipt-post", "spring/if-match-receipt-write", "spring/tenant-receipt-authorization"])

lesson("spring-security", "tenant-receipt-write", "Spring method security: reject a cross-tenant receipt mutation",
"A Spring method authorization rule can reject a tenant-scoped write before its service method changes state.", [
    ("Call through the managed service", ["The source-kit context enables method security and retrieves ReceiptWriter from the container. An authenticated tenant-east call changes its own receipt to reviewed. A tenant-west call through the same managed object throws AccessDeniedException; the west entry remains absent. This checks that the proxy applies the rule before entering the method.", "The test uses a local authentication token and a HashMap, not an HTTP request, real identity provider or repository query. The tenant argument comes from the caller in the fixture, so a production service must derive and validate tenant scope against trusted authentication and constrain its database UPDATE by tenant and receipt ID. [[spring/tenant-receipt-authorization|The read lesson]] covers the corresponding read boundary."]),
    ("Proxy rules have a call-path limit", ["A direct call within the same class can bypass proxy advice. Tests must obtain the managed bean and call the secured method through it. The rule also needs coverage for asynchronous work, event listeners and internal commands that may run without the same request security context. [[spring/proxy-self-invocation|Proxy self-invocation]] explains the dispatch boundary."])
], '''@PreAuthorize("#p0 == authentication.name")
public void change(String tenant, int receiptId, String next) {
    states.put(tenant + ":" + receiptId, next);
}''', "TenantReceiptWriteTest.managedServiceRejectsACrossTenantMutationBeforeTheMethodRuns",
"The in-memory write is expected O(1) average time and has no database isolation or persistence. The test proves this managed bean denies one cross-tenant mutation. It does not prove the HTTP filter, tenant mapping, database row scope or cross-process state.",
["Do not trust a tenant ID supplied only by the request body.", "Do not call the secured method through this when expecting proxy advice.", "Do not authorize a service and then issue an unscoped database UPDATE."],
["spring/tenant-receipt-authorization", "spring/method-authorization", "spring/idempotent-receipt-post"])

lesson("spring-production", "dependency-readiness", "Spring readiness: report an unavailable dependency without forcing liveness failure",
"A readiness check decides whether an instance should receive work; a liveness check asks whether restarting the instance is warranted.", [
    ("The local indicator changes state", ["The source kit injects a BooleanSupplier into a HealthIndicator. When the fixture's receipt store is available, health is UP; after it becomes unavailable, health is DOWN. That proves the indicator's local mapping only. A running Boot application still has to register it in the intended health group and expose that group through the deployment's probe configuration.", "A shared database outage can make every replica unready, which may be useful to stop new traffic but can also remove all endpoints from service. Putting the same external check into liveness can cause mass restarts while the database remains down. [[spring/actuator-health|Actuator health]] explains the public endpoint boundary. Design the probe after testing the orchestrator's behavior under dependency failure."]),
    ("Keep diagnostics private", ["The fixture returns only UP or DOWN. Internal exceptions, credentials, network addresses and detailed dependency state should not be published from a public health endpoint. A check also has a latency and load cost; a slow remote call on every probe can become its own outage trigger."])
], '''static class ReceiptStoreIndicator implements HealthIndicator {
    private final BooleanSupplier available;
    ReceiptStoreIndicator(BooleanSupplier available) { this.available = available; }
    @Override public Health health() {
        return available.getAsBoolean() ? Health.up().build() : Health.down().build();
    }
}''', "ReadinessIndicatorContractTest.localDependencyStateChangesTheIndicatorResult",
"A BooleanSupplier call is constant-time in the fixture. A real dependency probe needs a bounded timeout, concurrency budget and deployment test. This test does not wire the indicator into a readiness group or prove orchestrator behavior.",
["Do not add a shared external dependency to liveness without evaluating restart cascades.", "Do not expose internal connection details in public health responses.", "Do not assume a passing unit indicator test proves a deployed probe route."],
["spring/actuator-health", "spring/metric-cardinality", "spring/receipt-api-project"])

lesson("spring-testing", "mockmvc-standalone-scope", "Spring MockMvc standalone tests: know which HTTP layers were assembled",
"MockMvc standalone setup runs Spring MVC request handling for supplied controllers without loading the application's complete web context.", [
    ("The controller contract is still useful", ["The idempotency fixture sends POST requests through MockMvc and checks 400, 200 and 409 responses. It catches mapping, request-header and response mistakes in the controller. It does not load the application's security filter chain, datasource, production codec setup or reverse proxy. [[spring/idempotent-receipt-post|The replay lesson]] states its single-instance state limit.", "Use a full web application context or real HTTP test for claims about configured filters, authentication, CSRF, CORS, exception advice and endpoint wiring. Even that still does not test a deployment proxy or external identity provider. [[spring/testing-boundaries|Testing boundaries]] lays out the layers."]),
    ("Make evidence match the claim", ["A standalone test can check a controller's response policy quickly. A transaction test should obtain the proxied service from a context. A deployed behavior claim needs a deployment-level test. Run a rejected case as well as the success path; a page that only shows 200 misses the contract's most important branch."])
], '''var client = MockMvcBuilders.standaloneSetup(new ReceiptIntake()).build();
client.perform(post("/contract/idempotent-receipts")
        .contentType(MediaType.TEXT_PLAIN)
        .header("Idempotency-Key", "intake-41")
        .content("42"))
    .andExpect(status().isOk())
    .andExpect(content().string("receipt-1"));''', "IdempotentReceiptPostTest.replayReturnsTheOriginalReceiptAndConflictingPayloadIsRejected",
"Mock requests avoid a listening server and are fast, but speed is not coverage. The source-kit test checks MVC mapping on one supplied controller; its filter-chain and deployment assumptions need separate tests.",
["Do not infer production authentication from a standalone controller test.", "Do not call an in-memory MockMvc request a real network test.", "Do not omit the error branch when documenting an HTTP contract."],
["spring/mockmvc-tests", "spring/testing-boundaries", "spring/idempotent-receipt-post"])

lesson("spring-projects", "receipt-delivery-project", "Spring receipt delivery project: atomic write, guarded claim and replay",
"A receipt delivery workflow needs a durable business write, a pending event, a recoverable claim and a replay rule at the HTTP edge.", [
    ("Build in observable steps", ["First make one database transaction insert a receipt and its outbox row, then force an exception and verify both disappear. The source-kit [[spring/outbox-atomic-write|outbox test]] covers that local H2 boundary. Next claim the pending row with a guarded UPDATE and inspect its affected-row count. A failed or repeated claim must not be counted as new work.", "At the HTTP edge, send the same idempotency key and request twice and compare the receipt identifier. Reuse the key with a changed payload and require a conflict. The [[spring/idempotent-receipt-post|MockMvc fixture]] checks this in one JVM; a real application needs persistent replay storage and a trusted tenant scope. Protect updates with an authorized [[spring/if-match-receipt-write|revision precondition]]."]),
    ("Define the unfinished production boundary", ["Add claim tokens and expiry, an idempotent consumer keyed by event ID, bounded retries, dead-letter handling, migrations and target-database concurrency tests before calling delivery resilient. Test the crash windows around send and acknowledgement. A broker acknowledgement is not the same as consumer application success. Expose queue age and failures through bounded metrics, and treat readiness separately from liveness."])
], '''transaction.executeWithoutResult(status -> {
    jdbc.update("insert into receipt values (?, ?)", "R-41", "accepted");
    jdbc.update("insert into outbox values (?, ?, ?)", "E-41", "R-41", "pending");
});
int claimed = jdbc.update(
    "update outbox set state = 'claimed' where id = ? and state = 'pending'", "E-41");''', "OutboxWriteContractTest.receiptAndOutboxRowCommitOrRollBackTogether",
"The checked work uses one H2 process and one row. It is an acceptance seed, not a deployable delivery worker. Real throughput depends on database indexes, lock contention, batch size, broker latency and retry policy; none has been measured here.",
["Do not equate a claimed row with confirmed consumer delivery.", "Do not retry a create request without a stable operation key.", "Do not expose the source kit as a production receipt service."],
["spring/outbox-atomic-write", "spring/outbox-claim-state", "spring/idempotent-receipt-post", "spring/dependency-readiness"])

grouped = {
    "spring-data": ("Atomic business and delivery records", ["spring/outbox-atomic-write", "spring/outbox-claim-state"]),
    "spring-web": ("Replay and revision decisions", ["spring/idempotent-receipt-post", "spring/idempotency-vs-if-match"]),
    "spring-security": ("Tenant-scoped writes", ["spring/tenant-receipt-write"]),
    "spring-production": ("Dependency availability", ["spring/dependency-readiness"]),
    "spring-testing": ("Mock request evidence", ["spring/mockmvc-standalone-scope"]),
    "spring-projects": ("Receipt delivery workflow", ["spring/receipt-delivery-project"]),
}
for subject, (title, paths) in grouped.items():
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    hub["data"]["modules"].append({"title": title,
        "summary": "Run the source-kit fixture and inspect its rejected boundary.", "lessons": paths})
    hub["updated_at"] = stamp
    if "<h2>Section lessons</h2>" in hub["body"]:
        links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
            for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)",
            lambda match: match[1] + links + match[2], hub["body"])

reverse = {
    "spring/transaction-events": ["spring/outbox-atomic-write"],
    "spring/transactions": ["spring/outbox-atomic-write"],
    "spring/if-match-receipt-write": ["spring/idempotency-vs-if-match"],
    "spring/tenant-receipt-authorization": ["spring/tenant-receipt-write"],
    "spring/actuator-health": ["spring/dependency-readiness"],
    "spring/mockmvc-tests": ["spring/mockmvc-standalone-scope"],
    "java/jdbc-transactions": ["spring/outbox-atomic-write"],
    "java/exceptions": ["spring/idempotency-vs-if-match"],
}
for path, targets in reverse.items():
    row = by_path[path]
    marker = "<h2>Continue with Spring delivery contracts</h2>"
    row["body"] = row["body"].split(marker)[0] + marker + para("Continue with " + ", ".join(
        "[[" + target + "|" + by_path[target]["title"] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": added, "count": len(added)}))

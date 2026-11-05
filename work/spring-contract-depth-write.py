"""Add source-backed Spring transaction, MVC, async, cache and security lessons."""
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


def add(subject, slug, title, definition, sections, source, proof, cost, mistakes, related):
    specs.append(dict(subject=subject, path="spring/" + slug, slug=slug, title=title,
        definition=definition, sections=sections, source=source, proof=proof,
        cost=cost, mistakes=mistakes, related=related))


add("spring-data", "nested-savepoint", "Spring nested transactions: roll back one step to a JDBC savepoint",
"A nested transaction can roll back to a savepoint inside one physical JDBC transaction while the surrounding transaction continues.", [
    ("The outer write still has one final commit", ["The H2 fixture inserts accept, enters a nested step that inserts temporary-check and fails, then inserts record-rejection in the outer transaction. The result contains accept and record-rejection only. The nested failure is caught after Spring rolls back to its savepoint; it has not committed the outer work.", "This behavior needs a transaction manager and database path that support savepoints. The fixture explicitly enables nested transactions on a DataSourceTransactionManager. A second database, an HTTP call or a message broker cannot be rewound by that savepoint. [[spring/transactions|The outer transaction lesson]] explains the overall commit boundary."]),
    ("Do not swallow every failure", ["The catch is deliberate for a rejected optional step. If the nested failure means the entire command is invalid, propagate it so the outer transaction rolls back. If the outer write fails after the catch, all surviving rows still roll back together. A savepoint is a scoped rollback tool, not a replacement for input validation."])
], '''outer.executeWithoutResult(status -> {
    jdbc.update("insert into receipt_step values (?)", "accept");
    assertThrows(IllegalStateException.class, () -> nested.executeWithoutResult(child -> {
        jdbc.update("insert into receipt_step values (?)", "temporary-check");
        throw new IllegalStateException("reject nested step");
    }));
    jdbc.update("insert into receipt_step values (?)", "record-rejection");
});''', "NestedSavepointContractTest.nestedFailureRollsBackToSavepointWhileOuterWorkCommits",
"The fixture makes three small SQL writes and one savepoint. Its elapsed cost depends on the database and logging path; no throughput claim is made. The H2 result does not prove behavior on another driver or with JPA flush timing.",
["Do not call a savepoint an independent commit.", "Do not assume every transaction manager supports nested propagation.", "Do not catch a failure and continue when the outer command should fail."],
["spring/transaction-propagation", "spring/transactions", "spring/nested-vs-requires-new"])

add("spring-data", "nested-vs-requires-new", "Spring NESTED versus REQUIRES_NEW: savepoint or independent commit",
"NESTED keeps one physical transaction with savepoints; REQUIRES_NEW starts an independent physical transaction that can commit while its caller later rolls back.", [
    ("The persistence outcomes differ", ["In the new savepoint fixture, the failed child insert disappears and the outer rows commit. The existing [[spring/transaction-propagation|propagation fixture]] checks an independent inner commit surviving an outer rollback. That difference matters when writing audit rows, external work markers or compensating state. A surviving inner row may refer to business data that never committed.", "NESTED depends on savepoint support in the actual transaction manager and database driver. REQUIRES_NEW typically needs another database connection while the outer one remains bound; a pool sized only for active outer calls can stall under nested use. Neither mode coordinates a broker. [[spring/outbox-atomic-write|An outbox row]] should normally share the business transaction when atomicity is required."]),
    ("Test a state table, not only annotations", ["Draw the expected rows after inner failure, outer failure and success. Then run those branches against the target database. Proxy self-invocation can bypass annotation-based propagation, so obtain the managed service and invoke across the proxy boundary when testing @Transactional methods."])
], '''nested.setPropagationBehavior(TransactionDefinition.PROPAGATION_NESTED);
outer.executeWithoutResult(status -> {
    jdbc.update("insert into receipt_step values (?)", "accept");
    try {
        nested.executeWithoutResult(child -> {
            jdbc.update("insert into receipt_step values (?)", "temporary-check");
            throw new IllegalStateException("reject nested step");
        });
    } catch (IllegalStateException rejected) {
        jdbc.update("insert into receipt_step values (?)", "record-rejection");
    }
});''', "NestedSavepointContractTest.nestedFailureRollsBackToSavepointWhileOuterWorkCommits and FrameworkBoundaryTest.requiresNewAuditSurvivesOuterRollback",
"Two local H2 fixtures check one nested rollback and an independent propagation case. They do not establish pool capacity, target-database deadlock behavior or cross-service atomicity.",
["Do not expect a REQUIRES_NEW commit to roll back with its caller.", "Do not use NESTED when the underlying manager cannot create savepoints.", "Do not ignore the extra connection demand of independent inner transactions."],
["spring/nested-savepoint", "spring/transaction-propagation", "spring/outbox-atomic-write"])

add("spring-web", "mvc-validation-paths", "Spring MVC validation paths: object constraints and method parameters",
"Spring MVC can validate a request object and direct method parameters through different exception paths.", [
    ("One bad request can fail before the handler", ["The checked controller accepts a JSON receipt command with a nonblank note and a count query parameter of at least one. An empty note returns 400 on the object-validation path; count zero returns 400 on the method-validation path. Valid inputs reach the handler and return their expected values. The test supplies a validator explicitly to standalone MockMvc.", "An @Valid request object and a direct @Min parameter do not necessarily raise the same exception type. A handler that catches only MethodArgumentNotValidException can leave HandlerMethodValidationException with a different public shape. [[spring/mvc-validation-problem|The companion advice]] makes both return one bounded response. Nested objects need their own @Valid path and are covered separately in [[spring/nested-receipt-validation|nested validation]]."]),
    ("Validation is not authorization", ["A well-formed note and positive count say nothing about who may view or change a receipt. Authenticate, authorize and constrain persistence separately. Also bound raw request bytes and collections before expensive parsing; a field constraint does not protect the whole transport from oversized input."])
], '''record ReceiptCommand(@NotBlank String note) {}

@PostMapping(path = "/contract/validated-receipts", consumes = "application/json")
String create(@Valid @RequestBody ReceiptCommand command) { return command.note(); }

@GetMapping("/contract/receipt-limit")
String limit(@RequestParam @Min(1) int count) { return Integer.toString(count); }''', "MvcValidationModesTest.objectAndDirectParameterConstraintsRejectDifferentInputs",
"Constraint evaluation is small in this fixture, but validation cost depends on input size and custom validators. Standalone MockMvc checks local MVC mapping and validator behavior, not authentication, deployment request limits or the full application's advice registration.",
["Do not handle only one validation exception shape when a method has direct constraints.", "Do not assume @Valid by itself bounds raw request size.", "Do not treat a valid request body as an authorized operation."],
["spring/rest-validation", "spring/nested-receipt-validation", "spring/mvc-validation-problem"])

add("spring-web", "mvc-validation-problem", "Spring MVC validation errors: one public ProblemDetail for two failure paths",
"A controller advice can map object and direct-parameter validation failures to one stable ProblemDetail response.", [
    ("Keep the public response small", ["The source-kit advice handles MethodArgumentNotValidException and HandlerMethodValidationException. The test sends an empty JSON note and a count of zero; both produce HTTP 400 with the title Invalid receipt request. The handler leaves out raw submitted values and internal exception text. That makes the response predictable without leaking parser or validation internals.", "A production API should define a stable machine-readable type, field error keys, localization policy and correlation ID. Do not make the human title the only programmatic contract. [[spring/problem-details|The base ProblemDetail lesson]] covers the error envelope; [[spring/mvc-validation-paths|the validation-path lesson]] explains why two exception classes matter."]),
    ("Test the installed advice", ["This fixture registers advice explicitly with standalone MockMvc. That is enough for its mapping but does not prove the same advice is component-scanned into the running Boot application. A web-context test should assert registered advice and filters together. Avoid returning every validation message from third-party constraints without an output policy."])
], '''@RestControllerAdvice
static class ValidationAdvice {
    @ExceptionHandler({MethodArgumentNotValidException.class,
                       HandlerMethodValidationException.class})
    ProblemDetail invalidRequest(Exception rejected) {
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problem.setTitle("Invalid receipt request");
        problem.setDetail("Check the submitted fields and limits.");
        return problem;
    }
}''', "MvcProblemAdviceTest.twoValidationPathsReturnOnePublicErrorShape",
"The test checks two local 400 responses, not every invalid input, localization or production filter path. Advice code runs once per rejected request; large field-error lists need a deliberate bound before serialization.",
["Do not expose rejected secrets or stack traces in an error body.", "Do not assume standalone advice registration proves application component scanning.", "Do not let two validation paths return unrelated API shapes."],
["spring/mvc-validation-paths", "spring/problem-details", "spring/mockmvc-standalone-scope"])

add("spring-core", "async-future-failure", "Spring @Async futures: make worker failure observable to the caller",
"An @Async method returning CompletableFuture transfers completion or failure to a result the caller must inspect.", [
    ("The error is in the future", ["The checked service returns a failed future for receipt R-41. The caller obtains the managed bean from a Spring context and joins the returned future; the test observes CompletionException with the original IllegalStateException as its cause. The caller's original method invocation is not proof that delivery succeeded. A call that discards the future also discards its failure signal.", "Spring's proxy handles @Async only when the call crosses that proxy. A same-class call can run without asynchronous interception. The fixture intentionally checks the managed object; [[spring/proxy-self-invocation|the proxy lesson]] covers this dispatch rule. For void-returning @Async methods, failures need an uncaught-exception handler and cannot be joined by the caller in the same way."]),
    ("Async work still needs ownership", ["An executor needs a bounded queue, rejection policy and shutdown plan. A returned future also needs a timeout or cancellation policy at its owner. None of those makes work durable: if the process exits after the HTTP response, an in-memory task can disappear. Use [[spring/outbox-atomic-write|a committed outbox record]] for a delivery promise that must survive restart."])
], '''@Async
public CompletableFuture<String> deliver(String receiptId) {
    return CompletableFuture.failedFuture(
        new IllegalStateException("broker unavailable: " + receiptId));
}''', "AsyncFailureContractTest.failureIsObservedThroughTheReturnedFuture",
"The test checks one failed future from a local Spring context. It does not exercise a configured bounded executor, rejection under load, cancellation, actual broker I/O or process restart.",
["Do not equate method return with successful asynchronous delivery.", "Do not discard a future whose failure matters.", "Do not rely on proxy advice for a same-class method call."],
["spring/async-boundaries", "spring/proxy-self-invocation", "spring/outbox-atomic-write"])

add("spring-core", "async-vs-durable-delivery", "Spring async work versus durable delivery: separate latency from recovery",
"Asynchronous execution moves work away from the calling thread; durable delivery records work so it can be recovered after a process failure.", [
    ("A future is a live-process signal", ["The source-kit async fixture exposes an IllegalStateException through CompletableFuture.join. That is useful while the process and caller are alive. It does not give a new worker anything to retry after restart. The [[spring/async-future-failure|future lesson]] explains observation; the [[spring/outbox-atomic-write|outbox lesson]] commits a pending event with the receipt.", "A background worker can use both mechanisms: read a durable event, submit bounded work, inspect its result, then acknowledge under an ownership rule. If the send succeeds but acknowledgement fails, replay may repeat delivery. The consumer therefore needs a stable event ID and duplicate-tolerant behavior. Scheduling or @Async alone cannot close this crash window."]),
    ("Keep admission visible", ["A large unbounded executor queue can hide overload until memory pressure appears. Reject or shed work explicitly when capacity is full, and make an HTTP response reflect whether the operation is accepted durably or merely queued in memory. The current source kit demonstrates local executor rejection elsewhere but does not contain a production worker or broker."])
], '''CompletableFuture<String> result = dispatcher.deliver("R-41");
try {
    result.join();
} catch (CompletionException failed) {
    // The caller has observed a live-process failure; a durable retry still needs storage.
    throw failed;
}''', "AsyncFailureContractTest.failureIsObservedThroughTheReturnedFuture and OutboxWriteContractTest.receiptAndOutboxRowCommitOrRollBackTogether",
"A future holds completion state in memory. A database outbox adds write I/O, storage and worker scans. The two local tests verify a failure result and an atomic H2 write separately; they do not implement an end-to-end delivery service.",
["Do not return a durable-acceptance response for work only queued in RAM.", "Do not retry a broker send without a duplicate policy.", "Do not confuse an executor queue with an outbox table."],
["spring/async-future-failure", "spring/outbox-atomic-write", "spring/outbox-claim-state"])

add("spring-production", "cache-synchronized-loader", "Spring @Cacheable sync: collapse a local same-key cache miss",
"A synchronized cache load asks the configured cache provider to compute one value for concurrent calls with the same key.", [
    ("The loader count is the proof", ["The source-kit context enables caching with ConcurrentMapCacheManager and obtains ReceiptLookup through the container. Two calls for R-41 return the same value while the method body loads once. R-42 triggers a second load. The test checks the count; a cache-hit response without a count could hide duplicate work.", "The key must include every input that changes the result, including tenant scope where records differ. [[spring/cache-keys|Tenant cache keys]] cover that boundary. sync=true depends on provider support and applies at that provider's scope. This in-process manager cannot coordinate two replicas. It also does not supply expiry, capacity limits or distributed invalidation."]),
    ("Cold misses are not free", ["The callers waiting for a same-key load still consume request time and may exhaust upstream timeouts. A slow loader needs its own timeout and failure handling. If the loader fails, decide whether failures are cached, retried or surfaced; this fixture only checks successful values. [[spring/cache-eviction|Matched eviction]] matters after a write changes the underlying receipt."])
], '''@Cacheable(cacheNames = "receiptLookup", sync = true)
public String find(String receiptId) {
    loads.incrementAndGet();
    return "receipt:" + receiptId;
}''', "SynchronizedCacheContractTest.concurrentCallsForOneKeyUseOneLocalLoader",
"The map lookup is expected O(1) average time in this local provider, with memory proportional to distinct retained keys. The test checks two same-key calls and one different key; it does not measure contention, TTL, cross-instance coordination or failure caching.",
["Do not assume sync=true is a distributed lock.", "Do not omit tenant or representation inputs from the cache key.", "Do not call a cache miss cheap when the loader is slow or unbounded."],
["spring/cache-keys", "spring/cache-eviction", "spring/metric-cardinality"])

add("spring-security", "role-authority-prefix", "Spring Security roles and authorities: check the actual granted string",
"With the default role prefix, hasRole('EDITOR') checks for a granted authority named ROLE_EDITOR rather than EDITOR.", [
    ("The two tokens behave differently", ["The local method-security test first authenticates a reviewer with authority EDITOR. Calling the managed service is denied. Replacing it with ROLE_EDITOR permits the same method. The result is from a proxied service in a Spring context, not a string comparison inside the method body.", "An application can customize its role prefix, so document that configuration and test the actual authorities emitted by its authentication converter. For a claim that already carries an exact permission such as receipt:approve, hasAuthority can be clearer than a role shortcut. [[spring/jwt-resource-server|The JWT lesson]] checks token trust and scopes before any business authorization."]),
    ("A role is not record ownership", ["A reviewer role may permit an operation class but still should not modify every tenant's receipt. [[spring/tenant-receipt-write|Tenant-scoped writes]] need a trusted owner and a scoped database predicate. Method security can protect a service call, yet a same-class call through this bypasses proxy advice; test through the managed bean."])
], '''@PreAuthorize("hasRole('EDITOR')")
public String approve() { return "approved"; }''', "RoleAuthorityContractTest.roleRuleExpectsTheConfiguredRolePrefix",
"The test checks one default-prefix rule and two local authentication objects. It does not verify a JWT converter, remote issuer, HTTP filter chain, custom role hierarchy or database ownership.",
["Do not pass EDITOR when the configured rule expects ROLE_EDITOR.", "Do not assume hasRole implies row-level tenant permission.", "Do not test the plain target object when the rule is applied by a proxy."],
["spring/method-authorization", "spring/tenant-receipt-write", "spring/jwt-resource-server"])

add("spring-testing", "failure-layer-matrix", "Spring test failures: prove the layer that can reject the request",
"A useful Spring test chooses the narrowest execution layer that can observe the failure it claims to verify.", [
    ("The examples exercise different boundaries", ["Standalone MockMvc sees the two validation paths and the advice added to that builder. It does not prove the advice is discovered in the full application. A Spring application context is needed to see @Async and method-security proxy interception. H2 with a transaction manager is needed to see a savepoint rollback. A live HTTP or deployment test is needed to see network, filters and proxy behavior together.", "This is not a ranking of tests. The failure's owner determines the test. [[spring/mvc-validation-paths|MVC validation]], [[spring/async-future-failure|async completion]] and [[spring/nested-savepoint|nested rollback]] each have a different observable result. A unit test that calls the target method directly cannot establish that an interceptor applied."]),
    ("Record what did not run", ["When a rejected MVC input returns 400, assert that the handler did not mutate state. When a transaction throws, query the final rows. When a secured call is denied, check the target state. Status codes alone are weaker evidence than the side effects they are meant to prevent. Current fixtures cover local boundaries, not a production database or real authentication provider."])
], '''client.perform(get("/contract/receipt-limit").param("count", "0"))
    .andExpect(status().isBadRequest());
assertEquals(List.of("accept", "record-rejection"),
    jdbc.queryForList("select step from receipt_step order by step", String.class));''', "MvcValidationModesTest.objectAndDirectParameterConstraintsRejectDifferentInputs and NestedSavepointContractTest.nestedFailureRollsBackToSavepointWhileOuterWorkCommits",
"Focused tests are quick but omit layers by design. The two excerpts come from separate local fixtures; together they do not prove a complete web-to-database flow or deployment failure recovery.",
["Do not claim an HTTP filter was checked by a standalone controller test.", "Do not claim transaction rollback from an exception assertion alone; inspect rows.", "Do not call a direct target-method test proof of proxy advice."],
["spring/testing-boundaries", "spring/mockmvc-standalone-scope", "spring/nested-savepoint"])

def para(value: str) -> str:
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda found: '<a href="/' + found[1] + '">' + found[2] + "</a>", escaped) + "</p>"


all_titles = {path: row["title"] for path, row in by_path.items()}
all_titles.update({spec["path"]: spec["title"] for spec in specs})
for spec in specs:
    path = spec["path"]
    assert path not in by_path, path
    assert all(target in all_titles for target in spec["related"]), (path, spec["related"])
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == spec["subject"])
    body = para(spec["definition"])
    for heading, paragraphs in spec["sections"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(para(value) for value in paragraphs)
    body += '<h2>Checked source</h2><pre><code class="language-java">' + html.escape(spec["source"].strip(), quote=False) + "</code></pre>"
    body += "<h2>Verification boundary</h2>" + para(spec["proof"] + " runs in the downloadable Spring source kit. The excerpt omits imports and surrounding setup; the kit contains the complete tests.")
    body += "<h2>Costs and limits</h2>" + para(spec["cost"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2>" + para(", ".join("[[" + target + "|" + all_titles[target] + "]]" for target in spec["related"]) + ".")
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
        "related": [{"path": target, "title": all_titles[target]} for target in spec["related"]],
        "framework_version": "Spring Boot 4.0.8 / Spring Framework 7",
        "java_version": "21 source-kit baseline", "verification_suite": spec["proof"],
        "download_path": "/downloads/aitrove-spring-source-kit.zip"}
    rows.append(row)
    by_path[path] = row

grouped = {
    "spring-data": ("Savepoints and independent transactions", ["spring/nested-savepoint", "spring/nested-vs-requires-new"]),
    "spring-web": ("Validation and public errors", ["spring/mvc-validation-paths", "spring/mvc-validation-problem"]),
    "spring-core": ("Async completion and durability", ["spring/async-future-failure", "spring/async-vs-durable-delivery"]),
    "spring-production": ("Concurrent cache loads", ["spring/cache-synchronized-loader"]),
    "spring-security": ("Role and authority strings", ["spring/role-authority-prefix"]),
    "spring-testing": ("Match tests to failure layers", ["spring/failure-layer-matrix"]),
}
for subject, (title, paths) in grouped.items():
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    hub["data"]["modules"].append({"title": title,
        "summary": "Run the source-kit test and inspect the rejected case.", "lessons": paths})
    hub["updated_at"] = stamp
    if "<h2>Section lessons</h2>" in hub["body"]:
        links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(all_titles[path]) + "</a></li>"
            for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)",
            lambda found: found[1] + links + found[2], hub["body"])

reverse = {
    "spring/transaction-propagation": ["spring/nested-savepoint", "spring/nested-vs-requires-new"],
    "spring/rest-validation": ["spring/mvc-validation-paths"],
    "spring/problem-details": ["spring/mvc-validation-problem"],
    "spring/async-boundaries": ["spring/async-future-failure", "spring/async-vs-durable-delivery"],
    "spring/cache-keys": ["spring/cache-synchronized-loader"],
    "spring/method-authorization": ["spring/role-authority-prefix"],
    "spring/testing-boundaries": ["spring/failure-layer-matrix"],
    "java/completable-future": ["spring/async-future-failure"],
    "java/jdbc-transactions": ["spring/nested-savepoint"],
}
for path, targets in reverse.items():
    assert path in by_path, path
    row = by_path[path]
    marker = "<h2>Continue with checked Spring boundaries</h2>"
    row["body"] = row["body"].split(marker)[0] + marker + para("Continue with " + ", ".join(
        "[[" + target + "|" + all_titles[target] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [spec["path"] for spec in specs], "count": len(specs)}))

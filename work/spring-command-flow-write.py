"""Add original Spring tenant command lessons backed by the local contract suite."""
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


def add(subject, slug, title, opening, sections, code, proof, limits, mistakes, links):
    specs.append(dict(subject=subject, path="spring/" + slug, slug=slug,
        title=title, opening=opening, sections=sections, code=code,
        proof=proof, limits=limits, mistakes=mistakes, links=links))


add("spring-data", "tenant-command-transaction", "Spring tenant command transaction: keep state, event and replay record together",
"A tenant command transaction commits its receipt change, outbox event and replay record as one database unit.", [
    ("Three rows, one commit", ["The local command fixture starts with the same receipt ID in two tenants. A valid tenant-east token and receipt.write scope enter a managed service. The service binds tenant-east and R-41 to a versioned UPDATE, inserts an outbox event, then saves the response version under the tenant-scoped idempotency key. The accepted request leaves the east row at version 2, one event and one replay record. The west row stays unchanged.", "The service uses TransactionTemplate with a DataSourceTransactionManager. All three JDBC operations share one H2 DataSource and run on the request thread. A thrown exception after event insertion rolls back all three tables. Compare [[spring/outbox-atomic-write|the isolated outbox test]] with [[spring/command-rollback-proof|the combined rollback test]]. Neither makes external message delivery part of the database transaction."]),
    ("Keep identity outside client-controlled fields", ["The tenant argument reaches the service only after a method rule compares it with the validated JWT principal. The URL identifies requested work; it grants nothing. The SQL update includes tenant_id, receipt_id and expected version. Each predicate closes a different hole. See [[spring/tenant-jdbc-predicate|tenant-scoped SQL]] and [[spring/tenant-versioned-write|versioned mutation]]."])
], '''int changed = jdbc.update("update receipt_state set state = ?, version = version + 1 "
    + "where tenant_id = ? and receipt_id = ? and version = ?",
    nextState, trustedTenant, receiptId, expectedVersion);
if (changed != 1) throw new ResponseStatusException(HttpStatus.CONFLICT);''',
"TenantReceiptCommandFlowTest.authorizedWriteCommitsReceiptOutboxAndReplayRecord and TenantReceiptCommandFlowTest.failureAfterOutboxInsertRollsBackAllThreeTables",
"The proof uses one process and one H2 database. It does not establish multi-worker key races, target-database lock behavior, broker delivery, crash recovery or production migration safety. A transaction holds a connection and locks until commit; keep non-database I/O outside it.",
["Do not publish an event before the database transaction commits.", "Do not omit tenant_id from a write predicate.", "Do not equate a stored outbox row with delivered work."],
["spring/outbox-atomic-write", "spring/tenant-versioned-write", "spring/tenant-idempotency-key-scope", "spring/command-rollback-proof"])

add("spring-web", "tenant-idempotency-key-scope", "Spring POST idempotency keys: bind replay to tenant and command",
"A POST idempotency key identifies one accepted command within a defined ownership scope.", [
    ("Compare the full operation before replay", ["The fixture stores a replay row keyed by tenant_id and request_key. Its fingerprint covers receipt ID, requested state and expected version. Sending the same key and command twice returns the stored version 2 without another state change or outbox event. Reusing the key for a different state or another receipt returns 409. The second request does not become a new mutation merely because the first succeeded.", "The comparison happens before the versioned write. If it happened afterward, a legitimate retry could fail its own expected-version check. [[spring/idempotent-receipt-post|The earlier POST lesson]] checks local replay without this tenant-scoped command transaction. [[spring/tenant-command-transaction|The combined command]] commits the replay row with state and event."]),
    ("Choose retention and concurrency rules", ["The request key is required and bounded to a short ASCII token in this fixture. A production API needs a documented retention period, replay response contract and conflict policy. A unique database key must arbitrate concurrent first requests; this suite exercises sequential requests only. Also decide what happens when a key is reused after expiry. A fingerprint is an equality check, not a secret or an authorization decision."])
], '''String fingerprint = receiptId + ":" + nextState + ":" + expectedVersion;
List<StoredCommand> prior = jdbc.query(
    "select fingerprint, response_version from command_dedupe "
        + "where tenant_id = ? and request_key = ?",
    (row, index) -> new StoredCommand(row.getString(1), row.getInt(2)),
    trustedTenant, requestKey);
if (!prior.isEmpty()) {
    StoredCommand saved = prior.getFirst();
    if (!saved.fingerprint().equals(fingerprint))
        throw new ResponseStatusException(HttpStatus.CONFLICT);
    return saved.responseVersion();
}''',
"TenantReceiptCommandFlowTest.replayReturnsStoredVersionWithoutSecondMutation, TenantReceiptCommandFlowTest.reusedKeyWithDifferentCommandIsConflict and TenantReceiptCommandFlowTest.sameKeyCannotTargetAnotherReceipt",
"Only sequential local replay is tested. There is no concurrent request barrier, expiration job, response-body persistence or target-engine uniqueness test. The fixture's fingerprint uses validated short identifiers; a real API should canonicalize every behavior-affecting field before storing its digest.",
["Do not key replay by request key alone across tenants.", "Do not ignore the receipt ID when comparing commands.", "Do not run the version update before checking a legitimate replay."],
["spring/tenant-command-transaction", "spring/idempotent-receipt-post", "spring/idempotency-vs-if-match", "spring/tenant-command-api-project"])

add("spring-data", "tenant-versioned-write", "Spring JDBC versioned tenant update: inspect the affected row count",
"A versioned tenant update changes a row only when its owner, identifier and expected version all match.", [
    ("A zero-row update is a decision", ["The fixture issues one parameterized UPDATE with tenant_id, receipt_id and version in the WHERE clause. If it changes one row, the new version is returned. If it changes zero, the service returns 409 and writes no event or replay record. The stale-version test asks for version 3 while the stored row is version 1; the state remains new. A wrong tenant is denied before SQL, and the tenant predicate is still present as a storage boundary.", "This is compare-and-swap at one row. [[spring/if-match-receipt-write|The earlier If-Match lesson]] uses synchronized in-memory state; it is not a database atomicity proof. [[spring/jpa-optimistic-locking|JPA optimistic locking]] is another way to express a version contract, with different flush and exception timing."]),
    ("Separate absent from stale only when safe", ["A zero affected count can mean wrong version, missing ID or missing tenant ownership. The fixture returns one conflict response and does not disclose which condition occurred. A public API should choose its disclosure policy deliberately. Index the actual tenant-and-ID access path, then inspect the plan on the target database. H2 results cannot settle lock waits or deadlock behavior under concurrent load."])
], '''int changed = jdbc.update(
    "update receipt_state set state = ?, version = version + 1 "
        + "where tenant_id = ? and receipt_id = ? and version = ?",
    nextState, trustedTenant, receiptId, expectedVersion);
if (changed != 1) throw new ResponseStatusException(HttpStatus.CONFLICT);''',
"TenantReceiptCommandFlowTest.staleVersionLeavesNoOutboxRow and TenantReceiptCommandFlowTest.authorizedWriteCommitsReceiptOutboxAndReplayRecord",
"The H2 fixture checks one stale request and one accepted request. It does not run competing threads or prove behavior on the future target database. The update is a bounded indexed point operation in the fixture; verify real index selectivity and lock duration separately.",
["Do not select, compare and update in separate unprotected steps.", "Do not treat zero affected rows as a successful write.", "Do not reveal another tenant's row while explaining a conflict."],
["spring/tenant-command-transaction", "spring/if-match-receipt-write", "spring/jpa-optimistic-locking", "spring/tenant-jdbc-predicate"])

add("spring-data", "receipt-outbox-command", "Spring receipt outbox command: record intent without claiming delivery",
"A receipt outbox row records work to deliver after its business transaction commits.", [
    ("Commit intent with the receipt", ["The checked write inserts the outbox row after the versioned state update and before the replay record. TransactionTemplate commits the three operations together. A forced failure after the outbox insert rolls back both the event and the receipt update. That is the useful guarantee: no committed event for an uncommitted state in this one database transaction.", "The event ID includes tenant, receipt and request key in the local fixture; it is stable across a retry of the same command. [[spring/outbox-expiring-lease|The lease lesson]] covers a later worker claim, and [[spring/consumer-dedup-transaction|the consumer lesson]] covers duplicate handling. Neither is wired into this web context. The outbox row starts as a database fact, not a message delivered to a broker."]),
    ("Define the event contract", ["A real event needs a versioned schema, tenant-safe identifiers, ordering rules and a retention policy. Decide whether one receipt requires ordered delivery and how a consumer recognizes old or duplicate versions. Do not place an HTTP call inside the transaction to simulate atomic publication. That only holds a database connection while another system can fail independently."])
], '''transaction.execute(status -> {
    updateReceipt(trustedTenant, receiptId, expectedVersion, nextState);
    jdbc.update("insert into receipt_outbox values (?, ?, ?, ?)",
        eventId, trustedTenant, receiptId, nextState);
    saveReplay(trustedTenant, requestKey, responseVersion);
    return responseVersion;
});''',
"TenantReceiptCommandFlowTest.authorizedWriteCommitsReceiptOutboxAndReplayRecord and TenantReceiptCommandFlowTest.failureAfterOutboxInsertRollsBackAllThreeTables",
"The test has no relay, broker, external consumer, crash between claim and acknowledgement, or concurrent first command. Row storage and later polling add write and read load; capacity planning belongs to the target database and worker workload.",
["Do not call an inserted outbox row a delivered event.", "Do not do remote I/O inside the database transaction.", "Do not discard tenant identity from the event contract."],
["spring/tenant-command-transaction", "spring/outbox-atomic-write", "spring/outbox-expiring-lease", "spring/consumer-dedup-transaction"])

add("spring-testing", "command-rollback-proof", "Spring command rollback test: inspect state after an injected failure",
"A rollback test must inspect each protected table after a failure inside the transaction.", [
    ("Fail after the event insert", ["The local test invokes the managed command service with a test-only failure switch. The service updates the receipt, inserts an outbox row, then throws before saving its replay record. The assertion checks that the receipt still says new and both outbox and replay tables are empty. The exception alone would not prove rollback; the post-failure rows do.", "The test uses a real TransactionTemplate and DataSourceTransactionManager against H2. It exercises the service proxy's method authorization too, after setting a test security context. The HTTP tests separately exercise bearer validation and filter rules. [[spring/jwt-web-context-test|The JWT web test]] shows why direct service tests cannot replace filter-chain tests."]),
    ("Add other failure positions later", ["Try duplicate event IDs, a database timeout during replay insertion and a failure after commit before the client receives its response. The last case is why [[spring/tenant-idempotency-key-scope|replay]] matters. This test does not kill a process during commit or compare two independent database engines. Failure injection should be controlled in test configuration, never by a public request header."])
], '''assertThrows(IllegalStateException.class, () -> managedService.change(
    "tenant-east", "R-41", "rollback-41", command, true));
assertEquals("new", state("tenant-east"));
assertEquals(0, count("receipt_outbox"));
assertEquals(0, count("command_dedupe"));''',
"TenantReceiptCommandFlowTest.failureAfterOutboxInsertRollsBackAllThreeTables",
"This is a synchronous local rollback test, not a power-loss, broker or target-database crash test. It cannot show whether an external side effect already occurred, because the fixture performs none. Use a real database and process-level fault test before claiming recovery behavior.",
["Do not assert only that an exception was thrown.", "Do not make failure injection callable by an untrusted client.", "Do not confuse rollback before commit with recovery after commit."],
["spring/tenant-command-transaction", "spring/receipt-outbox-command", "spring/jwt-web-context-test", "spring/worker-recovery-test-matrix"])

add("spring-security", "bearer-post-csrf-boundary", "Spring Security bearer POST and CSRF: define the credential boundary",
"CSRF protection depends on how the browser supplies credentials to the endpoint.", [
    ("The fixture has no login cookie", ["The command test is a stateless bearer-token web context. A caller sends Authorization: Bearer explicitly; no server session or browser-sent Basic credential authenticates the POST. The fixture disables CSRF in that narrow context and requires receipt.write scope before the controller. The runnable ReceiptApplication is different: it retains Basic authentication and CSRF protection. Do not copy the fixture's CSRF setting into that application without changing its credential model.", "A signed tenant-east token targeting tenant-west is rejected by a managed method rule. The X-Tenant header says tenant-west in the accepted east request yet cannot override the principal. [[spring/jwt-tenant-principal|The principal lesson]] explains claim mapping; [[spring/scope-versus-tenant-access|the scope lesson]] separates filter and service denials."]),
    ("State what the browser can attach", ["If a browser app stores a token in a cookie and sends it automatically, the threat changes. Authentication alone does not replace origin and CSRF decisions. CORS determines which browser origins may read responses; it is not request authorization. For a real release, document token storage, permitted origins, cookie attributes and the deployed gateway's header rules before choosing CSRF configuration."])
], '''http.csrf(csrf -> csrf.disable())
    .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
    .authorizeHttpRequests(requests -> requests
        .requestMatchers("/contract/commands/**").hasAuthority("SCOPE_receipt.write"));''',
"TenantReceiptCommandFlowTest.authorizedWriteCommitsReceiptOutboxAndReplayRecord and TenantReceiptCommandFlowTest.crossTenantAndWrongScopeAreDeniedBeforeMutation",
"The local test has no browser, cookie, gateway, origin-policy or deployed token store. Its result only checks the stated stateless bearer setup. The production CSRF decision needs the actual client and credential transport design.",
["Do not disable CSRF in a cookie-authenticated application by copying this fixture.", "Do not treat CORS as authorization.", "Do not treat a signed token as permission for every tenant."],
["spring/security-filter-chain", "spring/jwt-tenant-principal", "spring/scope-versus-tenant-access", "spring/tenant-command-transaction"])

add("spring-exercises", "tenant-command-trace-exercise", "Spring exercise: trace tenant command replay, denial and rollback",
"A tenant command trace follows token validation, scope, owner rule, versioned SQL and transaction commit.", [
    ("Predict eight outcomes", ["Start with tenant-east and tenant-west holding R-41 at version 1. Submit accepted with version 1 and key accept-41 using an east write token. Repeat it unchanged. Reuse the key with held, then aim the east token at west, then send only receipt.read scope, then omit tenant_id, then use an unused key with expected version 3. For each request, record the status, east and west states, outbox count and replay count. Do not infer row state from HTTP status alone.", "The first request returns version 2 and adds one event. The replay returns version 2 without another event. Changed-command reuse and stale version return 409; cross-tenant and wrong-scope requests return 403; missing claim returns 401. [[spring/tenant-idempotency-key-scope|The replay lesson]] explains the first conflict. [[spring/tenant-versioned-write|The version lesson]] explains the second."]),
    ("Prove rollback", ["Run the test-only service failure after the outbox insert. Inspect all three tables, not just the exception. The source kit has no hosted judge, so the exercise runs with Maven on your machine. Add one new test for a second receipt ID sharing the same key and explain why the fingerprint must include that ID. The current fixture checks that conflict."])
], '''mvn -q -Dtest=TenantReceiptCommandFlowTest test''',
"TenantReceiptCommandFlowTest runs the accepted, replay, conflict, denial, stale-version and rollback cases",
"The trace is backed by a local MockMvc/H2 context with fixed claims and sequential requests. It cannot grade online submissions or prove multi-worker races. The command body is small; a real API must bound request bytes and validate every state transition.",
["Do not stop at a status-code assertion.", "Do not assume replay repeats a database update.", "Do not confuse the test-only injected failure with a client API option."],
["spring/tenant-command-transaction", "spring/tenant-idempotency-key-scope", "spring/tenant-versioned-write", "spring/command-rollback-proof"])

add("spring-projects", "tenant-command-api-project", "Spring Boot tenant command API project: assemble the local write path",
"A tenant command API links verified identity, authorization, versioned storage, replay and an outbox in one request path.", [
    ("The assembled fixture", ["The downloadable source kit now has one local web context that receives a signed tenant token, checks issuer, audience, expiry and tenant_id, requires receipt.write, applies a managed service owner rule, performs a versioned H2 update and commits the outbox and replay rows together. It verifies an accepted write, a replay, two key conflicts, stale version, cross-tenant denial, wrong scope, missing claim and rollback after event insertion. This closes the local composition gap between earlier isolated fixtures.", "This test configuration is not the runnable ReceiptApplication. That application still uses local Basic credentials and in-memory receipts. [[spring/tenant-receipt-api-security-plan|The migration plan]] explains the identity swap; [[spring/receipt-delivery-recovery-plan|the delivery plan]] covers worker work not assembled here."]),
    ("Release gates remain concrete", ["Move the schema into versioned migrations and run the same tests against the target database. Force concurrent first requests with the same key, prove the unique-key conflict path, then add a relay and idempotent consumer. Check crash/restart cases, issuer rotation, unknown tenant membership, load and deployed gateway behavior. Do not publish the local signing key or fixture credentials. The point of the current source kit is to let a reader inspect exact boundaries, not to supply a production service."])
], '''// Local checked flow: bearer -> scope -> owner -> versioned JDBC -> outbox + replay.
// Production work: real issuer, migrations, target DB, relay, consumer, recovery.
int responseVersion = managedService.change(
    trustedTenant, receiptId, requestKey, command, false);''',
"TenantReceiptCommandFlowTest runs eight local contract tests for the combined command path",
"No real identity provider, membership registry, deployment gateway, external broker, target database, concurrent request race or process crash is in this fixture. Transaction and JWT costs must be measured under the intended workload before capacity decisions.",
["Do not deploy test-generated RSA keys.", "Do not call the runnable Basic-auth app tenant-aware because this separate test exists.", "Do not claim a committed outbox row was delivered."],
["spring/tenant-command-transaction", "spring/tenant-receipt-api-security-plan", "spring/receipt-outbox-command", "spring/receipt-delivery-recovery-plan"])


def para(value: str) -> str:
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>", escaped) + "</p>"


titles = {path: row["title"] for path, row in by_path.items()}
titles.update({spec["path"]: spec["title"] for spec in specs})
for spec in specs:
    path = spec["path"]
    assert path not in by_path, path
    assert all(target in titles for target in spec["links"]), path
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == spec["subject"])
    body = para(spec["opening"])
    for heading, paragraphs in spec["sections"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(para(value) for value in paragraphs)
    language = "bash" if spec["subject"] == "spring-exercises" else "java"
    body += '<h2>Checked source</h2><pre><code class="language-' + language + '">' + html.escape(spec["code"].strip(), quote=False) + "</code></pre>"
    body += "<h2>Verification boundary</h2>" + para(spec["proof"] + " in the downloadable Spring source kit. The excerpt is shortened; the kit contains the complete test.")
    body += "<h2>Costs and limits</h2>" + para(spec["limits"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2>" + para(", ".join("[[" + target + "|" + titles[target] + "]]" for target in spec["links"]) + ".")
    row = by_path["spring/if-match-receipt-write"].copy()
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), type="article",
        path=path, title=spec["title"], summary=spec["opening"], body=body,
        subject=spec["subject"], difficulty="Intermediate", status="published",
        tags=["spring", "spring-boot", spec["slug"]], featured=False,
        sort_order=900 + len(rows), published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot", "section_path": hub["path"],
        "kind": "tutorial", "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "seo_ready": True,
        "related": [{"path": target, "title": titles[target]} for target in spec["links"]],
        "framework_version": "Spring Boot 4.0.8 / Spring Framework 7",
        "java_version": "21 source-kit baseline", "verification_suite": spec["proof"],
        "download_path": "/downloads/aitrove-spring-source-kit.zip"}
    rows.append(row)
    by_path[path] = row

grouped = {
    "spring-data": ("Tenant command transaction", ["spring/tenant-command-transaction", "spring/tenant-versioned-write", "spring/receipt-outbox-command"]),
    "spring-web": ("Command replay contract", ["spring/tenant-idempotency-key-scope"]),
    "spring-testing": ("Combined command failure proof", ["spring/command-rollback-proof"]),
    "spring-security": ("Stateless command security", ["spring/bearer-post-csrf-boundary"]),
    "spring-exercises": ("Tenant command trace", ["spring/tenant-command-trace-exercise"]),
    "spring-projects": ("Tenant command source kit", ["spring/tenant-command-api-project"]),
}
for subject, (title, paths) in grouped.items():
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    hub["data"]["modules"].append({"title": title,
        "summary": "Trace a tenant-scoped command from token to committed rows.", "lessons": paths})
    hub["updated_at"] = stamp
    if "<h2>Section lessons</h2>" in hub["body"]:
        links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
            for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)",
            lambda match: match[1] + links + match[2], hub["body"])

reverse = {
    "spring/tenant-receipt-api-security-plan": ["spring/tenant-command-api-project"],
    "spring/tenant-jdbc-predicate": ["spring/tenant-versioned-write"],
    "spring/outbox-atomic-write": ["spring/receipt-outbox-command"],
    "spring/idempotent-receipt-post": ["spring/tenant-idempotency-key-scope"],
    "spring/if-match-receipt-write": ["spring/tenant-versioned-write"],
    "spring/jwt-web-context-test": ["spring/command-rollback-proof"],
    "spring/receipt-api-project": ["spring/tenant-command-api-project"],
    "java/jdbc-transactions": ["spring/tenant-command-transaction"],
    "java/junit-tests": ["spring/command-rollback-proof"],
}
for path, targets in reverse.items():
    assert path in by_path, path
    row = by_path[path]
    marker = "<h2>Continue with checked tenant commands</h2>"
    row["body"] = row["body"].split(marker)[0] + marker + para("Continue with " + ", ".join(
        "[[" + target + "|" + titles[target] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [spec["path"] for spec in specs], "count": len(specs)}))

"""Add original Spring testing lessons to the local editorial fixture."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
rows = json.loads(FIXTURE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def prose(value):
    escaped = html.escape(value)
    return re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    )


lessons = [
    dict(
        slug="datajpa-test-flush-clear",
        title="Spring Data JPA test: flush and clear before trusting a read",
        summary="A persistence-context cache can make a repository test pass without proving that the database contains the expected row.",
        blocks=[
            ("Test the stored state", "A repository test saves a receipt, then calls findById in the same persistence context. JPA may hand back the already managed object. That proves little about column mapping, database defaults, or a query predicate. Flush pending SQL, clear the persistence context, then read again. A flush can expose a constraint failure, while the clear forces a later lookup to materialize data from the database. [[spring/jpa-saveandflush-not-commit|Flush remains different from commit]]."),
            ("Choose the assertion boundary", "For a derived tenant query, persist one local receipt and one foreign-tenant receipt, flush and clear, then assert only the local row appears. A unit mock cannot validate JPQL or the actual tenant predicate. For a test of [[spring/jpa-count-query-joins|joined page totals]], seed multiple matching child rows and assert both content and totalElements after clearing. Keep the dataset small enough to diagnose a failure, but varied enough to expose row multiplication."),
            ("Account for rollback", "@DataJpaTest normally wraps each test in a transaction and rolls it back. That isolates many repository tests, but it does not prove a commit-time constraint, an after-commit listener, or what another transaction sees. Use a separate committed-boundary test for those contracts. If you inspect SQL counts, reset the counter after setup; fixture inserts otherwise contaminate the measurement."),
        ],
        code='@DataJpaTest\nclass ReceiptTenantQueryTest {\n    @Autowired ReceiptRepository receipts;\n    @Autowired EntityManager entityManager;\n\n    @Test void excludesOtherTenantAfterDatabaseRoundTrip() {\n        receipts.save(ReceiptEntity.forTenant(NORTH_TENANT, "R-47"));\n        receipts.save(ReceiptEntity.forTenant(SOUTH_TENANT, "R-47"));\n        entityManager.flush();\n        entityManager.clear();\n\n        assertThat(receipts.findByTenantId(NORTH_TENANT))\n            .extracting(ReceiptEntity::getTenantId)\n            .containsExactly(NORTH_TENANT);\n    }\n}',
        cost="Flush adds a database synchronization point; clear discards managed objects and requires another read. That extra work is useful in persistence tests but would be needless ceremony in a plain unit test with no JPA context.",
        mistakes=["Do not assert against the same managed entity and call it a database round trip.", "Do not treat a rolled-back slice test as proof of commit-time behavior.", "Do not include setup statements in the query budget being measured."],
        related=["spring/jpa-saveandflush-not-commit", "spring/jpa-count-query-joins", "spring/jpa-specification-tenant-scope", "spring/datajpa-test-real-dialect", "spring/command-rollback-proof"],
    ),
    dict(
        slug="datajpa-test-real-dialect",
        title="Spring Data JPA test against the deployment database dialect",
        summary="Keep fast repository tests, then run dialect-sensitive SQL and migration cases against the actual database engine.",
        blocks=[
            ("An in-memory substitute changes the contract", "A query that passes against an embedded database can fail against the deployment engine because of SQL functions, locking, collation, JSON operators, generated columns, or index behavior. @DataJpaTest keeps the persistence slice small, while a database container gives the slice a realistic engine. Disable embedded-database replacement for that test. [[spring/testcontainers-service-connection-lifecycle|Container lifecycle]] and [[spring/testcontainers-migration-ownership|migration ownership]] still need explicit setup."),
            ("Select tests by risk", "Run ordinary mapping and simple query tests quickly. Put a smaller set of dialect-sensitive cases against the deployment engine: unique constraints, pessimistic locks, case-sensitive comparisons, pagination under joins, and migration compatibility. Compare the engine major version with production. A container image is not proof that production extensions, collation or configuration match; record those differences as test assumptions."),
            ("Force a database-specific failure", "Insert duplicate tenant and external-reference pairs, assert the database rejects the second write, then verify the transaction outcome. For a locking test, use two independent transactions and bounded timeouts, not two reads inside one test transaction. Inspect the SQL emitted by [[spring/jpa-entitygraph-toone-query|the fetch plan]] and the plan for [[spring/jpa-page-vs-slice|a bounded page]]."),
        ],
        code='@DataJpaTest\n@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)\n@Testcontainers\nclass ReceiptRepositoryDialectTest {\n    @Container\n    @ServiceConnection\n    static PostgreSQLContainer<?> database =\n        new PostgreSQLContainer<>("postgres:17");\n\n    @Autowired ReceiptRepository receipts;\n}',
        cost="A container adds startup time and memory use. Share an appropriate lifecycle across tests and reserve this path for behavior that depends on the real engine; do not trade away isolation by reusing dirty database state without cleanup.",
        mistakes=["Do not infer deployment SQL behavior from an embedded database alone.", "Do not run two lock participants in the same test transaction.", "Do not assume an engine version match also matches collation, extensions or schema migrations."],
        related=["spring/testcontainers-service-connection-lifecycle", "spring/testcontainers-migration-ownership", "spring/datajpa-test-flush-clear", "spring/jpa-entitygraph-toone-query", "spring/jpa-page-vs-slice"],
    ),
    dict(
        slug="http-test-transaction-boundary",
        title="Spring Boot HTTP test: client rollback does not own server writes",
        summary="A real HTTP server handles requests on another thread, so a test-managed transaction cannot be assumed to roll back those writes.",
        blocks=[
            ("Track the thread boundary", "A test starts a random-port Spring Boot server and calls POST /receipts. The test method may be annotated @Transactional, but the server processes the request on its own thread and transaction. Rolling back the test thread does not rewind the server's committed receipt. This differs from a repository slice where test and repository usually share the test-managed transaction. [[spring/transaction-thread-boundary|Transaction context]] is bound to its execution thread."),
            ("Own cleanup explicitly", "Give each test a unique tenant or receipt key and remove its rows through a controlled cleanup path, or reset an isolated database between tests. Query the database in a fresh transaction after the HTTP response so the assertion sees committed state. A MockMvc test can share more of the test thread, but it does not exercise the network stack; [[spring/mockmvc-tests|choose it for MVC behavior]], not a real port contract."),
            ("Test both success and failure", "For a command that writes a receipt and outbox event, assert both exist after a successful HTTP response. Then cause a database rejection and assert neither durable row remains. This proves [[spring/command-rollback-proof|the rollback invariant]] through the actual request path. Never rely on a cleanup rollback that runs only in the test thread."),
        ],
        code='@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)\n@AutoConfigureTestRestTemplate\nclass ReceiptHttpCommitTest {\n    @Autowired TestRestTemplate client;\n    @Autowired ReceiptRepository receipts;\n    String externalKey;\n\n    @Test void acceptedReceiptIsCommitted() {\n        externalKey = "receipt-http-" + UUID.randomUUID();\n        ResponseEntity<Void> response = client.postForEntity(\n            "/receipts", new ReceiptRequest(externalKey, 4700), Void.class);\n        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);\n        assertThat(receipts.existsByExternalKey(externalKey)).isTrue();\n    }\n\n    @AfterEach void removeCommittedFixture() {\n        if (externalKey != null)\n            receipts.findByExternalKey(externalKey).ifPresent(receipts::delete);\n    }\n}',
        cost="A real server test loads the full context and opens a port. It is slower than a repository or MVC slice, so use it for behavior that crosses HTTP, transaction and persistence boundaries; isolate its committed data deliberately.",
        mistakes=["Do not expect a test-method rollback to undo a server-thread commit.", "Do not leave committed test rows for later tests to discover.", "Do not claim a MockMvc-only test proved real HTTP listener behavior."],
        related=["spring/transaction-thread-boundary", "spring/command-rollback-proof", "spring/mockmvc-tests", "spring/datajpa-test-flush-clear", "spring/transactions"],
    ),
    dict(
        slug="mockmvc-security-filter-path",
        title="Spring MockMvc security test: run the application filter chain",
        summary="A controller assertion is not an authorization test unless the request passes through the configured security chain.",
        blocks=[
            ("Keep the filter path real", "A controller test calls a handler with a mocked principal and gets the expected JSON. That does not show whether the deployed SecurityFilterChain permits the route, checks a bearer token, or rejects a missing tenant claim. Build MockMvc from the application context with security filters active, or use a full-context auto-configured MockMvc. [[spring/mockmvc-standalone-scope|Standalone setup]] is useful for mapping logic but needs explicit filter wiring."),
            ("Assert a denial matrix", "Send an anonymous request, a caller with a valid identity but missing authority, and a caller with authority for the wrong tenant. Assert status and absence of writes for each. A helper that injects a mock JWT can exercise authorization rules, but it skips cryptographic token decoding; use a separate test for the decoder configuration. [[spring/jwt-web-context-test|JWT web-context tests]] and [[spring/security-filter-chain|filter-chain rules]] divide those responsibilities."),
            ("Watch the service boundary", "A passing HTTP 403 does not prove a scheduled job or message listener is protected. Test [[spring/method-security-proxy-boundary|method authorization]] through a Spring-injected bean as well. For the web test, verify that a rejected request does not call the write service. Avoid mocking the SecurityFilterChain itself; doing so removes the behavior under examination."),
        ],
        code='@SpringBootTest\n@AutoConfigureMockMvc\nclass ReceiptAuthorizationHttpTest {\n    @Autowired MockMvc mvc;\n\n    @Test void rejectsMissingWriteAuthority() throws Exception {\n        mvc.perform(post("/receipts")\n                .with(jwt().authorities(\n                    new SimpleGrantedAuthority("SCOPE_receipt.read")))\n                .with(csrf())\n                .contentType(MediaType.APPLICATION_JSON)\n                .content("{\\"externalKey\\":\\"R-47\\",\\"minorUnits\\":4700}"))\n            .andExpect(status().isForbidden());\n    }\n}',
        cost="A full-context MockMvc test starts more beans than a web slice and still avoids a real network port. Keep a small denial matrix here; use focused service tests for detailed tenant and policy permutations.",
        mistakes=["Do not bypass the filter chain and call the result an HTTP authorization test.", "Do not treat a mock JWT as proof of signature or issuer validation.", "Do not rely only on controller security when non-web callers reach the same service."],
        related=["spring/security-filter-chain", "spring/jwt-web-context-test", "spring/mockmvc-standalone-scope", "spring/method-security-proxy-boundary", "spring/http-test-transaction-boundary"],
    ),
    dict(
        slug="test-context-cache-shape",
        title="Spring TestContext cache: keep equivalent tests on one context shape",
        summary="Profiles, property overrides, bean overrides and test configuration affect whether Spring can reuse an application context.",
        blocks=[
            ("A cached context has a key", "Two integration tests that request equivalent configuration can share one cached ApplicationContext inside a test process. Add a different active profile, a per-class property, or a distinct @MockitoBean override and the cache key may differ; startup work repeats. The cache is process-local, so separate build forks do not share it. [[spring/context-testing|Context tests]] should prove wiring, not create a fresh application for every assertion."),
            ("Consolidate by contract", "Group tests that need the same profile, database connection and bean graph. Use explicit fixtures and reset test data between methods instead of changing properties merely to alter a row value. Avoid @DirtiesContext as routine cleanup: it evicts the context and makes later tests pay startup cost again. Never share mutable singleton test state across classes without reset; a fast reused context must still be isolated at the data and mock level."),
            ("Measure before restructuring", "Enable test-context cache statistics while running the suite and inspect hit, miss and eviction counts. Change one configuration dimension at a time, then rerun the same set. A context cache hit is useful only if the test still covers production-relevant wiring. [[spring/testcontainers-service-connection-lifecycle|Container ownership]] can add its own lifecycle and property differences."),
        ],
        code='@SpringBootTest\n@ActiveProfiles("integration")\n@Transactional\nabstract class ReceiptIntegrationContext {\n    @Autowired protected ReceiptRepository receipts;\n}\n\nclass ReceiptLookupIT extends ReceiptIntegrationContext {\n    @Test void tenantQueryDoesNotLeakRows() {\n        UUID north = UUID.randomUUID();\n        UUID south = UUID.randomUUID();\n        receipts.save(ReceiptEntity.forTenant(north, "R-47"));\n        receipts.save(ReceiptEntity.forTenant(south, "R-48"));\n        assertThat(receipts.findByTenantId(north))\n            .extracting(ReceiptEntity::getTenantId)\n            .containsExactly(north);\n    }\n}',
        cost="Context startup can dominate a small test suite. Reuse saves startup time and memory, while overly broad contexts increase the cost of each miss. Cache size and build forking limit the benefit; measure suite wall time, not annotation count.",
        mistakes=["Do not add per-class profile or property overrides without recognizing the cache-key cost.", "Do not use @DirtiesContext as a substitute for fixture cleanup.", "Do not share unreset mutable state just to gain a cache hit."],
        related=["spring/context-testing", "spring/mockito-bean-proxy-caveat", "spring/testcontainers-service-connection-lifecycle", "spring/testing-boundaries", "spring/boot-config-process-test-boundary"],
    ),
    dict(
        slug="mockito-bean-proxy-caveat",
        title="Spring @MockitoBean override: a mock can remove advice from the tested bean",
        summary="Replace a collaborator for a boundary test, but keep the advised service real when verifying transactions, caching or method security.",
        blocks=[
            ("Choose which bean is under test", "@MockitoBean replaces a bean in the Spring test context. The replacement is a Mockito object, not the original advised service. A controller test may safely mock a receipt service while checking request validation and response mapping. A test that claims to verify @Transactional, @Cacheable or @PreAuthorize on that same mocked service is empty: the method body and its advice have been removed. [[spring/proxy-self-invocation|Proxy mechanics]] still matter in the real service."),
            ("Keep the seam narrow", "Mock an external gateway or a downstream collaborator, then invoke the real Spring-managed service when testing service advice. Use a spy only with care: a spy can retain an advised proxy shape, but stubbing and verification around proxies are easy to misunderstand. An integration test with a real repository is stronger evidence for [[spring/command-rollback-proof|rollback]] than verification that a mock repository method was called."),
            ("Check the override itself", "If several beans share a type, qualify the intended replacement explicitly; a test can fail at context startup or replace an unintended bean. Count distinct override combinations across classes because each can alter [[spring/test-context-cache-shape|context caching]]. State in the test name what remains real and what has been substituted."),
        ],
        code='@SpringBootTest\nclass ReceiptServiceAdviceTest {\n    @Autowired ReceiptWriteService realService;\n    @Autowired ReceiptRepository receipts;\n    @MockitoBean PaymentGateway paymentGateway;\n\n    @Test void failedChargeLeavesNoReceipt() {\n        String externalKey = "rejected-" + UUID.randomUUID();\n        when(paymentGateway.charge(any())).thenThrow(\n            new PaymentDeclinedException("declined"));\n        assertThatThrownBy(() -> realService.accept(\n            new ReceiptCommand(externalKey, 4700)))\n            .isInstanceOf(PaymentDeclinedException.class);\n        assertThat(receipts.existsByExternalKey(externalKey)).isFalse();\n    }\n}',
        cost="A mock keeps the test local and fast, but replacing a bean changes the graph and may create another cached context. A database assertion costs more than mock verification and is warranted when the claim is about committed or rolled-back state.",
        mistakes=["Do not mock the service whose transaction or authorization advice you claim to test.", "Do not assume a Mockito interaction proves durable database state.", "Do not leave bean selection ambiguous when several candidates share a type."],
        related=["spring/proxy-self-invocation", "spring/command-rollback-proof", "spring/test-context-cache-shape", "spring/method-security-proxy-boundary", "spring/context-testing"],
    ),
    dict(
        slug="transaction-event-commit-test",
        title="Spring transactional event test: cross an actual commit boundary",
        summary="An AFTER_COMMIT listener cannot be proved by a test transaction that always rolls back.",
        blocks=[
            ("The phase is the behavior", "A service publishes ReceiptAccepted inside a transaction and an @TransactionalEventListener with AFTER_COMMIT starts follow-up work. A test method annotated @Transactional rolls back by default, so the listener should not run in that test. Verifying only that publishEvent was called does not prove after-commit delivery. [[spring/transaction-events|Transaction events]] separate event publication from phase execution."),
            ("Commit in a controlled test", "Use TestTransaction to mark the active test transaction for commit and end it, then assert a synchronous listener's observable result. Or run the service without a test-managed transaction and verify committed state in a fresh transaction. Do not send irreversible external traffic from a unit test; substitute the final gateway while keeping the service, transaction manager and listener real. For durable cross-process delivery, [[spring/relay-transaction-boundaries|an outbox]] remains the stronger contract."),
            ("Cover rollback too", "Invoke the service on a path that throws after publication, and assert the AFTER_COMMIT listener did not perform its action. If the listener is asynchronous, wait on a bounded observable completion signal rather than sleeping a guessed duration. Test both commit and rollback with the same event type so a misplaced plain @EventListener cannot quietly pass."),
        ],
        code='@SpringBootTest\n@Transactional\nclass ReceiptCommittedEventTest {\n    @Autowired ReceiptWriteService receipts;\n    @Autowired ReceiptNotificationProbe probe;\n\n    @Test void notifiesOnlyAfterCommit() {\n        receipts.accept(new ReceiptCommand("R-47", 4700));\n        assertThat(probe.count()).isZero();\n        TestTransaction.flagForCommit();\n        TestTransaction.end();\n        assertThat(probe.count()).isEqualTo(1);\n    }\n}',
        cost="A commit test writes durable rows and needs cleanup or isolated data. It is slower than a publisher mock but exercises the phase that matters. An asynchronous listener adds a scheduling boundary and needs bounded synchronization.",
        mistakes=["Do not expect AFTER_COMMIT to fire after a test transaction rolls back.", "Do not equate publishEvent invocation with listener completion.", "Do not use an unbounded sleep to wait for asynchronous delivery."],
        related=["spring/transaction-events", "spring/relay-transaction-boundaries", "spring/http-test-transaction-boundary", "spring/command-rollback-proof", "spring/relay-failure-trace"],
    ),
    dict(
        slug="scheduled-worker-fixed-clock-test",
        title="Spring scheduled worker test: inject a clock and call the work once",
        summary="Test a due-time rule without waiting for a real scheduler tick or relying on wall-clock races.",
        blocks=[
            ("Separate trigger from work", "@Scheduled decides when to call a method. A reminder worker decides which due rows to claim and how many to process. Put that decision in a callable service with an injected Clock; keep the scheduled adapter small. A test can advance a fixed clock and call one work cycle directly. [[spring/scheduled-outbox-worker|The scheduled outbox pattern]] still needs database ownership rules across replicas."),
            ("Make time a precise input", "At 09:47 UTC, a reminder due exactly at 09:47 should be included if the contract says dueAt less than or equal to now. Seed one row just before, one equal, and one after the boundary. Assert a bounded batch of 47 and the resulting state. Do not use Thread.sleep or depend on the CI machine timezone. Test [[spring/poller-shutdown|shutdown and draining]] separately because a fixed clock does not exercise scheduler lifecycle."),
            ("Keep concurrency in another test", "A direct call proves selection logic, not that two application replicas cannot claim the same row. Use an integration test with two independent workers and a real database lock or claim update for that invariant; [[spring/poller-integration-tests|poller integration tests]] cover it. Capture failures as retryable state rather than letting a scheduled method's exception lose a work item."),
        ],
        code='final class ReminderWorker {\n    private final Clock clock;\n    private final ReminderStore reminders;\n\n    ReminderWorker(Clock clock, ReminderStore reminders) {\n        this.clock = clock;\n        this.reminders = reminders;\n    }\n\n    int runOneCycle() {\n        return reminders.claimDueBeforeOrAt(clock.instant(), 47).size();\n    }\n}\n\nclass ReminderWorkerClockTest {\n    @Test void usesFixedCutoff() {\n        Instant cutoff = Instant.parse("2026-10-05T09:47:00Z");\n        ReminderStore store = mock(ReminderStore.class);\n        when(store.claimDueBeforeOrAt(cutoff, 47)).thenReturn(List.of());\n        Clock fixed = Clock.fixed(cutoff, ZoneOffset.UTC);\n        assertThat(new ReminderWorker(fixed, store).runOneCycle()).isZero();\n        verify(store).claimDueBeforeOrAt(cutoff, 47);\n    }\n}',
        cost="A fixed clock removes waiting and makes boundary tests fast. It does not replace a database concurrency test or a scheduler lifecycle test; those cost more because they exercise real threads and storage ownership.",
        mistakes=["Do not sleep until a scheduled tick in a unit test.", "Do not let system timezone decide a UTC due-time assertion.", "Do not mistake a single-worker fixed-clock test for multi-replica claim safety."],
        related=["spring/scheduled-outbox-worker", "spring/poller-integration-tests", "spring/poller-shutdown", "spring/poller-batch-limit", "spring/worker-recovery-test-matrix"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
for number, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    body += ('<h2>Implementation contract</h2><pre><code class="language-java">'
             + html.escape(item["code"], quote=False) + "</code></pre>")
    body += "<h2>Cost and verification</h2><p>" + prose(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(
        "<li>" + prose(mistake) + "</li>" for mistake in item["mistakes"]
    ) + "</ul>"
    body += "<h2>Read next</h2><p>" + ", ".join(
        '<a href="/' + target + '">' + html.escape(titles[target]) + "</a>"
        for target in item["related"]
    ) + ".</p>"
    row = copy.deepcopy(by_path["spring/component-scan-vs-bean"])
    row.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path, title=item["title"], summary=item["summary"], body=body,
        subject="spring-testing", tags=["spring", "spring-boot", "testing", item["slug"]],
        sort_order=5600 + number, published_at=stamp, created_at=stamp,
        updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": "spring/testing",
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7 where relevant",
        "java_version": "21 or later",
        "verification_suite": "Spring test API contract review; snippets require an application model and test dependencies",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

paths = ["spring/" + item["slug"] for item in lessons]
hub = by_path["spring/testing"]
hub["data"]["modules"].append({
    "title": "Spring testing boundaries",
    "summary": "Persistence, HTTP, security, cache, commit-event and scheduler tests.",
    "lessons": paths,
})
for route in ("spring/testing", "spring/spring-boot"):
    entry = by_path[route]
    entry["body"] += "<h2>Spring testing boundaries</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    entry["updated_at"] = stamp

for source, target in [
    ("spring/jpa-saveandflush-not-commit", "spring/datajpa-test-flush-clear"),
    ("spring/testcontainers-service-connection-lifecycle", "spring/datajpa-test-real-dialect"),
    ("spring/transaction-thread-boundary", "spring/http-test-transaction-boundary"),
    ("spring/security-filter-chain", "spring/mockmvc-security-filter-path"),
    ("spring/context-testing", "spring/test-context-cache-shape"),
    ("spring/proxy-self-invocation", "spring/mockito-bean-proxy-caveat"),
    ("spring/transaction-events", "spring/transaction-event-commit-test"),
    ("spring/scheduled-outbox-worker", "spring/scheduled-worker-fixed-clock-test"),
]:
    entry = by_path[source]
    entry["body"] += ('<h2>Test this boundary</h2><p><a href="/' + target + '">'
                      + html.escape(titles[target]) + "</a></p>")
    entry["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring testing lessons")

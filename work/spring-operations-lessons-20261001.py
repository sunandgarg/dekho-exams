"""Add original Spring operations lessons with deliberate curriculum links."""

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
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    )


lessons = [
    dict(
        slug="gateway-circuit-breaker-fallback", section="spring/web-apis",
        title="Spring Cloud Gateway circuit breaker: a fallback is an API response contract",
        summary="A Gateway circuit breaker can forward to a local fallback, but the fallback must state what data it can still guarantee.",
        blocks=[
            ("A healthy edge can still serve the wrong answer", "Suppose the inventory service times out while a shopper asks for available stock. A local fallback that returns zero units looks like a confirmed out-of-stock result, although no such result was observed. Use an explicit unavailable response or a clearly marked stale snapshot. The CircuitBreaker Gateway filter can forward to a local route with a forward: URI; it does not make the downstream write safe to repeat. [[spring/gateway-retry-body-budget|Retry limits]] and [[spring/cloud-circuit-breaker|circuit state]] serve different purposes."),
            ("Keep the failure domain small", "Name the breaker for the downstream dependency or operation whose failures should be counted together. A shared breaker for every route can turn one failing catalog call into a checkout outage. The fallback controller should avoid calling the same dependency. If it reads a cache, define the maximum accepted age and include that age in the response contract. [[spring/redis-cache-ttl-vs-tti|Cache expiry]] alone does not prove freshness."),
            ("Prove each state transition", "Test a slow downstream, an immediate 503, an open breaker, and recovery after the dependency responds again. Assert both the status and response body. Verify a protected route still passes authentication before fallback. This example configures routing only; the breaker implementation, thresholds, and timeout need an application test."),
        ],
        code='- id: inventory-read\n  uri: ${INVENTORY_SERVICE_URI}\n  predicates:\n    - Path=/api/inventory/**\n  filters:\n    - name: CircuitBreaker\n      args:\n        name: inventoryRead\n        fallbackUri: forward:/fallback/inventory', language="yaml",
        cost="A breaker adds state checks per call and can reduce load on an unhealthy dependency. A fallback that reads another remote service can move, rather than remove, the failure and latency cost.",
        mistakes=["Do not turn an unknown stock count into a factual zero.", "Do not send a write request to a success-shaped fallback without a recovery contract.", "Do not share one circuit breaker across unrelated downstream services."],
        related=["spring/cloud-circuit-breaker", "spring/gateway-retry-body-budget", "spring/redis-cache-ttl-vs-tti", "spring/gateway-filter-ordering"],
    ),
    dict(
        slug="gateway-route-refresh-access", section="spring/production",
        title="Spring Cloud Gateway route refresh: guard the actuator write boundary",
        summary="A route definition change is not active until the route cache refreshes; the write-capable actuator endpoint needs restricted access.",
        blocks=[
            ("Distinguish stored routes from active routes", "A team updates a route definition so /api/ledger points to a new service. A successful write to a route store does not prove the Gateway instance now routes traffic there. The route cache must refresh, and each instance must observe the intended definition. The Gateway actuator can expose a POST refresh operation, but its access is disabled by default; read-only exposure is safer for ordinary operations."),
            ("Make route changes reviewable", "Keep a versioned route manifest and apply it through a controlled deployment or authenticated operator path. Do not expose unrestricted route creation to the public network: a malicious route can redirect requests or strip headers. Read the effective routes after refresh, probe the new upstream, and retain the previous manifest for rollback. [[spring/gateway-filter-ordering|Filter order]] and [[spring/cloud-gateway-tenant|tenant routing]] can change when a route definition changes."),
            ("Test partial rollout", "Update one Gateway replica while another still has the old route. Send requests through both and record the selected route ID and destination. Then test a malformed definition and an asynchronous refresh failure. A 200 from the refresh endpoint is not proof that every replica has converged; verify the effective route list and a real request."),
        ],
        code='management:\n  endpoint:\n    gateway:\n      access: read-only\n  endpoints:\n    web:\n      exposure:\n        include: gateway', language="yaml",
        cost="Route verification adds control-plane requests during rollout. An unrestricted management endpoint can turn a configuration error into a traffic or security incident.",
        mistakes=["Do not publish write-capable Gateway actuator endpoints without operator authentication and network restriction.", "Do not infer fleet-wide convergence from one instance's refresh response.", "Do not overwrite an existing actuator-managed route ID without following its update contract."],
        related=["spring/cloud-gateway-tenant", "spring/gateway-filter-ordering", "spring/health-probe-security", "spring/gateway-circuit-breaker-fallback"],
    ),
    dict(
        slug="redis-cluster-slot-boundary", section="spring/production",
        title="Spring Data Redis Cluster: key slots change multi-key operations",
        summary="A Redis Cluster key maps to a hash slot; a command involving keys in different slots can fail even when each key exists.",
        blocks=[
            ("One key is not the whole cluster", "A catalog cache that worked against standalone Redis may fail after clustering when a script or multi-key command touches product:47 and tenant:west:47 in different slots. The client can follow redirects for single-key operations, but that does not make cross-slot operations legal. Hash tags can deliberately colocate related keys, for example {tenant-west}:product:47 and {tenant-west}:price:47. Use that only when the operation truly needs same-slot execution; overloading one slot can create a hot shard."),
            ("Scan each shard with care", "A raw KEYS command on one cluster node sees that node's keys, not the whole cluster. Spring's cluster connection exposes cluster-wide operations, but a broad scan still consumes work across nodes. [[spring/redis-cache-writer-races|Region-wide cache clearing]] deserves a measured plan. Do not use keyspace events as a global deletion log: cluster event subscriptions are node-local and can miss other shards."),
            ("Exercise a real cluster", "Run a two-key operation with keys in distinct slots and assert a clean failure. Repeat with keys sharing a hash tag. During resharding, measure redirection count and latency. A standalone Redis integration test cannot prove slot behavior, so the code below documents a key rule rather than claiming an executed cluster test."),
        ],
        code='String stockKey = "{tenant-west}:stock:47";\nString priceKey = "{tenant-west}:price:47";\n// The shared hash tag places these keys in one cluster slot.\n// Keep unrelated tenants on different tags.',
        cost="Same-slot multi-key work is possible, but concentrating too many keys on one tag limits shard distribution. Cluster-wide scans grow with the total keyspace and node count.",
        mistakes=["Do not assume a multi-key command works because both single-key reads work.", "Do not treat a one-node KEYS result as a full-cluster inventory.", "Do not rely on keyspace events for complete cluster-wide change delivery."],
        related=["spring/redis-cache-key-schema", "spring/redis-cache-writer-races", "spring/redis-cache-failover-policy", "spring/session-redis-replicas"],
    ),
    dict(
        slug="redis-cache-failover-policy", section="spring/production",
        title="Spring Redis cache outage: choose failure behavior per operation",
        summary="An unavailable Redis cache should have an explicit response policy; cache reads and shared sessions have different failure costs.",
        blocks=[
            ("Classify the dependency", "A public catalog read may continue by loading from the database when Redis is down, provided the database can absorb the extra load. A session lookup cannot safely invent an authenticated user when the shared session store is unavailable. A rate limiter might fail closed for a protected write but use a carefully bounded emergency policy for a read-only endpoint. One global catch-and-ignore CacheErrorHandler does not express these differences."),
            ("Protect the fallback", "If every replica bypasses cache at once, the backing store sees a synchronized miss storm. Limit concurrent loads, keep a short timeout, and shed excess requests before database capacity is consumed. [[spring/cache-synchronized-loader|Local synchronized loading]] helps only within one process. [[spring/gateway-authenticated-rate-limit|Gateway limits]] can protect the edge, while [[spring/dependency-readiness|readiness]] must reflect whether the operation can still meet its contract."),
            ("Test both recovery directions", "Disconnect Redis under steady load, verify the chosen HTTP status and backing-store saturation, then reconnect it. Check that keys refill at a bounded rate and that stale values are not accepted after a write. For [[spring/session-redis-replicas|shared sessions]], verify failover at the login boundary separately from cache behavior. The pseudocode is a policy sketch, not a generic cache interceptor."),
        ],
        code='PriceQuote quote(String tenantId, String sku) {\n    try {\n        return cacheLookup(tenantId, sku)\n            .orElseGet(() -> boundedDatabaseLoad(tenantId, sku));\n    } catch (RedisConnectionFailureException unavailable) {\n        return boundedDatabaseLoad(tenantId, sku);\n    }\n}\n// Bound concurrent database loads before enabling this policy.',
        cost="Bypassing cache shifts latency and load to the source. Concurrency caps and a short deadline protect that source but may reject requests that would otherwise wait.",
        mistakes=["Do not swallow every Redis error and call the operation successful.", "Do not treat an absent session as an authenticated principal during failover.", "Do not reopen the entire database floodgate after Redis reconnects."],
        related=["spring/redis-cache-writer-races", "spring/session-redis-replicas", "spring/dependency-readiness", "spring/gateway-authenticated-rate-limit"],
    ),
    dict(
        slug="stomp-relay-availability", section="spring/web-apis",
        title="Spring STOMP broker relay: credentials and broker availability are separate from user identity",
        summary="The relay holds broker TCP connections with configured credentials, while the browser's user identity comes from HTTP authentication.",
        blocks=[
            ("Two kinds of connection", "The relay keeps a system connection for application-originated messages and a broker connection for each connected WebSocket client. It sets configured broker login and passcode values on forwarded CONNECT frames; browser-supplied STOMP credentials are not the trusted user identity. [[spring/stomp-handshake-identity|Handshake authentication]] and destination authorization still decide which browser may send or subscribe. Broker credentials belong in secret configuration, not browser JavaScript."),
            ("Know when the system link is down", "The relay emits BrokerAvailabilityEvent when its system connection changes availability. A producer should not report a notification as delivered merely because it called a messaging template while the broker was unavailable. Persist required events first and retry delivery from durable state. The relay reconnects, but reconnecting does not replay an event that the application failed to store. [[spring/stomp-broker-scale-boundary|Multi-instance routing]] and [[spring/stomp-reconnect-snapshot|client recovery]] complete the path."),
            ("Test a broker interruption", "Connect two browsers through separate app replicas, stop the broker, attempt an application notification, then restore it. Assert an availability signal, bounded producer behavior, reconnection, and reconciliation of missed data. The configuration sketch omits TLS and credential rotation; those need deployment tests."),
        ],
        code='registry.enableStompBrokerRelay("/topic", "/queue")\n    .setRelayHost("broker.internal")\n    .setSystemLogin(systemLogin)\n    .setSystemPasscode(systemPasscode)\n    .setClientLogin(clientLogin)\n    .setClientPasscode(clientPasscode);',
        cost="Each WebSocket client adds a broker TCP connection. Broker capacity and application socket capacity must both cover peak concurrent sessions; reconnection can create a burst after an outage.",
        mistakes=["Do not put broker passcodes in STOMP frames sent by the browser.", "Do not treat broker availability as proof a particular client received a message.", "Do not assume reconnection replays application events that were never persisted."],
        related=["spring/stomp-handshake-identity", "spring/stomp-broker-scale-boundary", "spring/stomp-reconnect-snapshot", "spring/relay-dead-letter"],
    ),
    dict(
        slug="stomp-reconnect-snapshot", section="spring/web-apis",
        title="Spring WebSocket reconnect: recover state after an unobserved gap",
        summary="A renewed STOMP subscription resumes live delivery; it does not reconstruct messages sent while the browser was disconnected.",
        blocks=[
            ("Detect the gap", "A dashboard receives stock version 84, loses its socket, and reconnects when the current version is 91. Subscribing again may receive only version 92 onward. The browser must fetch a snapshot or request durable events after 84 before declaring itself current. The version belongs to the business data, not to the WebSocket frame transport. [[spring/stomp-broker-scale-boundary|An external broker]] improves cross-node routing but does not by itself define offline replay."),
            ("Order snapshot and stream", "One approach subscribes first, then requests a snapshot and discards live frames at or below the snapshot version. Another obtains a snapshot with a resumable cursor and then subscribes from that cursor if the broker supports it. Either way, define duplicate handling, tenant scope, and what happens when the cursor is too old. [[spring/stomp-handshake-identity|Destination authorization]] must be checked for both the socket and the snapshot HTTP endpoint."),
            ("Test with a deliberate disconnect", "Publish versions 84 through 91 while the browser is offline. Reconnect through a different application instance. Assert the client ends at version 91 or later without applying an older update after a newer one. Simulate a missing version and force a fresh snapshot. The client pseudocode captures the ordering rule; a browser and broker integration test remains necessary."),
        ],
        code='if (incoming.version() <= currentVersion) return;\nif (incoming.version() != currentVersion + 1) {\n    requestFreshSnapshot();\n    return;\n}\napplyStockUpdate(incoming);\ncurrentVersion = incoming.version();',
        cost="Snapshots add one read on reconnect; durable replay adds storage and cursor management. Either is cheaper than silently displaying a wrong stock count after a network gap.",
        mistakes=["Do not assume a new SUBSCRIBE replays frames sent during disconnection.", "Do not apply an older frame after a newer snapshot.", "Do not expose another tenant's snapshot through a cursor or destination name."],
        related=["spring/stomp-broker-scale-boundary", "spring/stomp-relay-availability", "spring/stomp-handshake-identity", "spring/graphql-tenant-read"],
    ),
    dict(
        slug="http-service-groups", section="spring/web-apis",
        title="Spring HTTP service groups: configure one host policy for several interfaces",
        summary="A group collects HTTP service interfaces that share one client setup, such as a target host, credentials and timeout policy.",
        blocks=[
            ("Group by transport policy", "A pricing API may expose QuoteClient and DiscountClient on the same host. Register both in one HTTP service group when they share base URL, authentication and connection policy. A payments client with a tighter timeout or distinct credentials belongs in another group even if its host happens to match. Spring Framework can declare groups with @ImportHttpServices and apply configuration through an HTTP service group configurer. [[spring/http-service-client-contract|The annotated interface]] still describes only the request shape."),
            ("Watch duplicate types", "If the same interface is registered under two groups, injection by interface type becomes ambiguous. Resolve it by group through the proxy registry or use distinct interfaces. A broad package scan can unintentionally include a new interface during a rollout; explicit registration is easier to review for a small client surface. [[spring/oauth2-client-token-scope|Token scope]] must match the group that owns the remote call."),
            ("Test the intended host", "Bring up two local stub servers and give each group a different base URL. Assert QuoteClient reaches the pricing server and the payments interface reaches the payment server, including failure status handling. A unit test that calls a mocked interface cannot detect a group wired to the wrong host. The snippet declares the group; the transport configurer is application-specific."),
        ],
        code='@Configuration\n@ImportHttpServices(group = "pricing",\n    types = {QuoteClient.class, DiscountClient.class})\nclass RemotePricingClients {\n    // Configure the pricing group base URL, auth and timeouts together.\n}',
        cost="Grouping removes repeated client setup but can broaden the impact of a bad shared timeout or credential. Keep metrics by remote operation even when clients share one pool.",
        mistakes=["Do not group clients solely because their Java interfaces sit in one package.", "Do not inject a duplicated interface by type without resolving its group.", "Do not assume group registration supplies a correct base URL or timeout automatically."],
        related=["spring/http-service-client-contract", "spring/restclient-timeout-budget", "spring/http-service-client-retry-boundary", "spring/oauth2-client-token-scope"],
    ),
    dict(
        slug="webclient-response-ownership", section="spring/web-apis",
        title="Spring WebClient exchangeToMono: decode the response inside its callback",
        summary="The response passed to exchangeToMono has a bounded ownership window; choose a body decoder or error path before returning.",
        blocks=[
            ("Inspect status with the body in scope", "A shipping service returns 200 with a label, 404 when a parcel is missing, and 503 during maintenance. exchangeToMono lets the caller choose a decoder by status. After the returned publisher completes, any unconsumed response body is released; code farther downstream cannot decode it later. Return a domain error for known 404 and a service error for 5xx. [[spring/restclient-status-no-retry|Status policy]] should be consistent across blocking and reactive clients."),
            ("Keep size and time bounded", "A bodyToMono call can buffer a response into memory. Choose a maximum in-memory size and a connection/read timeout suited to the payload. A reactive chain does not make an unbounded body safe. For a stream, use Flux and preserve backpressure rather than collecting every item. [[spring/restclient-timeout-budget|The deadline budget]] still includes waiting for a pooled connection, remote work and decoding."),
            ("Exercise disposal and status", "Return a 503 with a body, a malformed 200 body, and a response that never completes. Assert typed errors and that the connection pool remains usable after each case. The snippet shows a status branch; exact error mapping and codecs need a stub-server integration test."),
        ],
        code='return shippingClient.get().uri("/labels/{parcelId}", parcelId)\n    .exchangeToMono(response -> {\n        if (response.statusCode().value() == 200) {\n            return response.bodyToMono(ShippingLabel.class);\n        }\n        if (response.statusCode().value() == 404) {\n            return Mono.error(new ParcelMissing(parcelId));\n        }\n        return response.createError();\n    });',
        cost="Decoding a whole body retains up to the configured buffer limit. Leaking connections or allowing unlimited responses reduces throughput well before CPU is saturated.",
        mistakes=["Do not save ClientResponse for body decoding after exchangeToMono completes.", "Do not treat every non-200 response as a missing parcel.", "Do not collect an unbounded response stream into one List."],
        related=["spring/http-service-client-contract", "spring/restclient-status-no-retry", "spring/restclient-timeout-budget", "spring/reactive-http-service-client"],
    ),
    dict(
        slug="reactive-http-service-client", section="spring/web-apis",
        title="Reactive HTTP service client: the proxy returns a publisher, not a completed call",
        summary="An HTTP service interface backed by WebClient starts remote work on subscription and inherits cancellation and timeout behavior.",
        blocks=[
            ("Subscription owns the attempt", "A method returning Mono<PriceQuote> can describe a remote request without sending it yet. If two callers subscribe independently to a cold result, two HTTP attempts may occur. If the downstream commits a write, repeating subscription has the same uncertainty as [[spring/http-service-client-retry-boundary|a retry]]. Keep a stable command ID for writes and avoid hidden subscribe calls inside handlers."),
            ("Cancellation is not a remote rollback", "A browser disconnect or timeout can cancel the local publisher after the request reached the remote service. The remote side may still complete. For read-only calls, cancellation mainly affects resource use and latency. For a write, reconcile by command ID or query a durable result. [[spring/reactive-transaction-context-ownership|Reactive transactions]] protect local database work in their chain; they cannot roll back a separate HTTP service."),
            ("Make the boundary testable", "Back the interface with a WebClient adapter, then test against a stub that delays a response and records received requests. Subscribe twice and count attempts; cancel after the server receives a POST and verify the application reports uncertainty rather than false failure. The code creates a proxy but does not supply production timeouts or authentication."),
        ],
        code='@HttpExchange("/v1/prices")\ninterface ReactivePricingClient {\n    @GetExchange("/{sku}")\n    Mono<PriceQuote> quote(@PathVariable String sku);\n}\nvar adapter = WebClientAdapter.create(webClient);\nvar client = HttpServiceProxyFactory.builderFor(adapter).build()\n    .createClient(ReactivePricingClient.class);',
        cost="Non-blocking I/O can support many pending calls with fewer request threads, but each active call still consumes a connection and buffers. Timeouts and concurrency limits remain necessary.",
        mistakes=["Do not call subscribe inside a controller and return before the remote result is known.", "Do not assume cancellation undoes a remote write.", "Do not reuse a cold publisher as though it were a cached result."],
        related=["spring/http-service-client-contract", "spring/http-service-client-retry-boundary", "spring/webclient-response-ownership", "spring/reactive-transaction-context-ownership"],
    ),
    dict(
        slug="testcontainers-migration-ownership", section="spring/testing",
        title="Spring Boot Testcontainers and Flyway: let one owner prepare the test schema",
        summary="A container supplies a database endpoint; the application still needs a deterministic migration owner before repository tests run.",
        blocks=[
            ("Connection is not schema", "@ServiceConnection can give a test ApplicationContext the container's database connection details. It does not prove that the target schema exists or that Flyway migrations succeeded. When Spring Boot owns Flyway startup, it should apply the same versioned migrations that production uses before repository beans exercise the database. A test that creates tables manually can hide an incompatible production migration. [[spring/flyway-boot-ownership|Migration ownership]] matters as much as container startup."),
            ("Fail on history drift", "Run a clean database through all migrations and assert the expected schema. Then run an upgrade from a retained prior schema to catch changes that only fail during rollout. Flyway checksums should not be repaired automatically to make a red test green; [[spring/flyway-history-checksum|history integrity]] must remain visible. If a test fixture needs data, insert it after migrations through a named helper, not through a second schema creator."),
            ("Observe two failure types", "Break a migration and assert context startup fails before the first repository call. Separately, keep migrations valid but make a repository query incompatible with a column type; assert the query fails. The container snippet from [[spring/testcontainers-service-connection-lifecycle|service connections]] remains unchanged; the verification concerns who owns the schema."),
        ],
        code='@SpringBootTest\n@Import(InventoryDatabaseTestConfig.class)\nclass InventoryRepositoryMigrationTest {\n    @Autowired JdbcTemplate database;\n\n    @Test void migrationsAppliedBeforeRepositoryStarts() {\n        Integer completed = database.queryForObject(\n            "SELECT COUNT(*) FROM flyway_schema_history WHERE success = true",\n            Integer.class);\n        assertNotNull(completed);\n        assertTrue(completed > 0);\n    }\n}',
        cost="A real database and migrations increase test startup time, but they exercise SQL syntax, constraints and schema history that an in-memory substitute may miss.",
        mistakes=["Do not assume a running container means migrations passed.", "Do not repair a checksum in tests to hide an edited applied migration.", "Do not mix Flyway ownership with a second automatic schema creator without a clear order."],
        related=["spring/testcontainers-service-connection-lifecycle", "spring/flyway-boot-ownership", "spring/flyway-history-checksum", "spring/boot-flyway-test-scope"],
    ),
    dict(
        slug="testcontainers-parallel-isolation", section="spring/testing",
        title="Spring Testcontainers parallel tests: one database can leak another test's rows",
        summary="Sharing a database container across test classes saves startup time but requires data and transaction isolation between concurrent tests.",
        blocks=[
            ("A shared port is not a private database", "Two test classes can reuse the same Spring context and PostgreSQL container. If both insert order 47 and one truncates a table in @BeforeEach, the result depends on scheduling. A rollback annotation on the test method does not clean work done by a worker thread or a separate transaction. [[spring/transaction-thread-boundary|Thread-bound transactions]] and [[spring/requires-new-connection-budget|new transactions]] make that leak easy to miss."),
            ("Pick one isolation mechanism", "Use unique tenant and command IDs per test when assertions can filter by them. For tests that verify global counts or migration state, use a separate database, schema, or serialized suite; do not rely on a random sleep. Keep cleanup tied to the fixture it created and never truncate shared tables while parallel tests run. [[spring/testcontainers-migration-ownership|Migrations]] should be applied once by the chosen context owner, not raced by every test class."),
            ("Run the hostile schedule", "Start both classes in parallel. Pause one test after insert, let the other complete its cleanup, then release the first and assert its row remains. Repeat with a worker that commits outside the test transaction. The code documents unique IDs; CI must still run the actual parallel schedule for this guarantee."),
        ],
        code='String tenantId = "test-" + UUID.randomUUID();\nledger.insert(tenantId, "order-47", 23);\nassertEquals(23, ledger.totalForTenant(tenantId));\n// Cleanup only rows owned by tenantId.',
        cost="Unique test data is cheap but can grow a long-lived container's tables. Separate schemas or containers cost startup time and memory but give stronger isolation for global-state tests.",
        mistakes=["Do not truncate a shared database from a parallel test's setup or cleanup.", "Do not assume test rollback covers @Async work or REQUIRES_NEW scopes.", "Do not claim parallel safety from a sequential local run."],
        related=["spring/testcontainers-service-connection-lifecycle", "spring/testcontainers-migration-ownership", "spring/transaction-thread-boundary", "spring/requires-new-connection-budget"],
    ),
    dict(
        slug="oauth2-client-token-scope", section="spring/security",
        title="Spring OAuth2 client tokens: bind the authorized client to the intended caller and host",
        summary="A RestClient or WebClient OAuth2 interceptor can attach a token automatically; the chosen principal and registration define whose token it sends.",
        blocks=[
            ("A default can cross the wrong boundary", "A shared WebClient configured to use the currently authorized OAuth2 client by default can attach the user's token to every request it makes, including a newly added host. Resolve the client registration deliberately at the call site, or use one client per trusted downstream. A client-credentials token represents the application, while an authorization-code token represents a user session. [[spring/oauth2-client-token-lifecycle|Refresh and storage]] follow the selected authorized client, not the Java HTTP interface."),
            ("Keep the principal key stable", "Spring Security's authorized-client manager stores tokens under a principal identity and registration. A background job without the request's SecurityContext must use an explicit service principal; pretending it is the last browser user is a data-leak risk. For a user-delegated call, verify that the target service, scopes and tenant match the current caller. [[spring/http-service-groups|HTTP service groups]] are a useful place to constrain hosts and client setup."),
            ("Test both identities", "Send one request as operator A, another as operator B, and inspect only the test server's received Authorization header claims. Then run a scheduled job and verify it uses its own client-credentials registration. Do not log raw tokens in production. The interface sketch names the call but leaves the OAuth2 filter configuration to the application's security setup."),
        ],
        code='return reportsWebClient.get()\n    .uri("/v1/reports/{reportId}", reportId)\n    .attributes(clientRegistrationId("reports-service"))\n    .retrieve()\n    .bodyToMono(ReportView.class);',
        cost="Token acquisition and refresh add network calls at expiry; sharing a wrong token has a security cost far beyond that latency. Cache authorized clients by the correct principal and registration.",
        mistakes=["Do not enable a default OAuth2 token on a client used for arbitrary hosts.", "Do not reuse a browser user's authorized client in background work.", "Do not treat client credentials as proof of an end user's tenant or permission."],
        related=["spring/oauth2-client-token-lifecycle", "spring/http-service-groups", "spring/http-service-client-contract", "spring/tenant-claim-required"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {
    "spring/production": "spring-production",
    "spring/web-apis": "spring-web",
    "spring/security": "spring-security",
    "spring/testing": "spring-testing",
}
for number, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    body += ('<h2>Implementation sketch</h2><pre><code class="language-' + item.get("language", "java")
             + '">' + html.escape(item["code"], quote=False) + "</code></pre>")
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
        subject=subjects[item["section"]],
        tags=["spring", "spring-boot", item["section"].split("/")[-1], item["slug"]],
        sort_order=5000 + number, published_at=stamp, created_at=stamp, updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7 / Spring Cloud Gateway 5 where relevant",
        "java_version": "21 or later",
        "verification_suite": "Official API contract review; implementation sketch not compiled",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

headings = {
    "spring/production": "Route changes and Redis operations",
    "spring/web-apis": "Remote boundaries and recovery",
    "spring/security": "Outbound token ownership",
    "spring/testing": "Container schema and test isolation",
}
for section, heading in headings.items():
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({
        "title": heading,
        "summary": "Follow the operation through failure, recovery and linked tests.",
        "lessons": paths,
    })
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["spring/spring-boot"]
parent["body"] += "<h2>Operations and recovery contracts</h2><ul>" + "".join(
    '<li><a href="/spring/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons
) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("spring/cloud-circuit-breaker", "spring/gateway-circuit-breaker-fallback"),
    ("spring/cloud-gateway-tenant", "spring/gateway-route-refresh-access"),
    ("spring/redis-cache-key-schema", "spring/redis-cluster-slot-boundary"),
    ("spring/stomp-broker-scale-boundary", "spring/stomp-relay-availability"),
    ("spring/http-service-client-contract", "spring/http-service-groups"),
    ("spring/testcontainers-service-connection-lifecycle", "spring/testcontainers-migration-ownership"),
    ("spring/oauth2-client-token-lifecycle", "spring/oauth2-client-token-scope"),
]:
    row = by_path[source]
    row["body"] += ('<h2>Related boundary</h2><p><a href="/' + target + '">'
                    + html.escape(titles[target]) + "</a></p>")
    row["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring articles; new total", sum(
    row["path"].startswith("spring/") and row["type"] == "article" for row in rows
))

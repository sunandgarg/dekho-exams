"""Add original Spring cache, edge, messaging, client and test lessons."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

root = pathlib.Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def paragraph(value):
    escaped = html.escape(value)
    return re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    )


lessons = [
    dict(
        slug="redis-cache-ttl-vs-tti", section="spring/production",
        title="Spring Redis cache TTL versus idle expiry: GETEX changes the read contract",
        summary="Redis cache TTL expires after a write; time-to-idle refreshes on eligible reads and needs an explicit Redis and client contract.",
        blocks=[
            ("Pick the clock before the annotation", "A quote lookup cached for 47 seconds should expire 47 seconds after its last write if it is allowed to become stale regardless of traffic. That is TTL. A session-like lookup that stays alive while actively read needs time-to-idle. Spring Data Redis can opt into idle expiry through Redis GETEX, which reads and resets expiry in one operation. GETEX requires Redis 6.2 or newer. A normal GET from another client does not refresh that idle clock. If one code path uses Spring Cache and another reads Redis directly, the observed lifetime changes with the route taken."),
            ("Keep the refresh boundary visible", "Configure one cache by name and give it a finite entry TTL. Turn on idle behavior only when every read path participates in the same rule. A cache hit is not an authorization check: [[spring/cache-keys|include tenant identity in the key]] and still check the caller's rights. If a quote must become invalid immediately after a price edit, use [[spring/cache-eviction|eviction]] or a versioned key; waiting for either expiry clock is a business decision."),
            ("Test time without a production outage", "Write a value, advance beyond the configured TTL, and assert a miss. For idle behavior, read before expiry, advance again, and assert the entry survives only when GETEX was used. Run the test against the actual Redis version, since an in-memory fake cannot establish command support. This is a configuration sketch, not a live Redis test."),
        ],
        code='RedisCacheConfiguration quotes = RedisCacheConfiguration.defaultCacheConfig()\n    .entryTtl(Duration.ofSeconds(47))\n    .disableCachingNullValues();\n// For a separate cache with idle semantics:\nRedisCacheConfiguration activeQuotes = quotes.enableTimeToIdle();',
        cost="A cache read is one Redis round trip, but idle refresh writes expiry metadata on each GETEX hit. Hot keys stay resident; size and eviction pressure can rise. Expiry does not coordinate concurrent misses across replicas.",
        mistakes=["Do not describe TTL as resetting after every cache hit.", "Do not enable time-to-idle against a Redis server that lacks GETEX.", "Do not assume a raw GET refreshes an entry's idle expiry."],
        related=["spring/cache-keys", "spring/cache-eviction", "spring/cache-synchronized-loader", "spring/session-redis-replicas"],
    ),
    dict(
        slug="redis-cache-key-schema", section="spring/production",
        title="Spring Redis cache key schema: tenant, prefix and rollout version",
        summary="A Redis cache key is a shared wire format across instances, deployments and tenants; changing it needs a rollout plan.",
        blocks=[
            ("Treat the key as persisted data", "Two service instances using the same Redis database can read each other's entries. The default cache-name prefix separates caches, but it does not separate tenants inside a cache. A key built only from productId can return tenant A's pricing to tenant B if the method's result also depends on tenantId. [[spring/cache-keys|Cache key design]] is part of the security boundary, not an optimization detail."),
            ("Version representation changes", "If the cached value's shape changes between deployments, an older binary may fail to deserialize a newer value while both are live. Put a schema version in the cache namespace, use an explicit serializer, and set a finite TTL so old entries retire. Avoid relying on Java native serialization for an untrusted or cross-language cache. A rolling deployment may temporarily hold both v3 and v4 keys; budget the extra memory. [[spring/redis-cache-ttl-vs-tti|Expiry policy]] determines how long that overlap lasts."),
            ("Check the collision matrix", "Test two tenants with the same product ID, two cache names with the same method argument, and both application versions during a rolling release. Inspect the exact bytes or strings written to Redis; a mocked CacheManager cannot prove namespace isolation. The code sketches the key contract, while the project's serializer choice remains explicit application work."),
        ],
        code='@Cacheable(cacheNames = "price-v4",\n    key = "#tenantId + \u0027:\u0027 + #productId")\npublic PriceQuote quote(String tenantId, String productId) {\n    return pricing.load(tenantId, productId);\n}',
        cost="Versioned keys temporarily duplicate hot values during rollout. Tenant-specific keys increase cardinality; that memory cost is preferable to returning another tenant's result.",
        mistakes=["Do not omit a parameter that changes the returned value from the key.", "Do not disable key prefixes when cache names share one Redis database.", "Do not roll out an incompatible value serializer under an unchanged namespace."],
        related=["spring/cache-keys", "spring/redis-cache-ttl-vs-tti", "spring/cache-eviction", "spring/tenant-claim-required"],
    ),
    dict(
        slug="redis-cache-writer-races", section="spring/production",
        title="Spring Redis cache writer: compound operations and replica stampedes",
        summary="A local synchronized cache loader and Redis writer settings do not automatically create one cross-instance computation.",
        blocks=[
            ("Name the race", "During a catalog refresh, six replicas miss the same key. Each may call the catalog database before any replica writes its result. [[spring/cache-synchronized-loader|A synchronized loader]] may coordinate callers inside one process, but it is not a distributed single-flight guarantee. Spring Data Redis's usual non-locking cache writer also allows multi-command put-if-absent and clear sequences to overlap. Its optional locking writer locks a cache region, not one key, so a busy cache can serialize unrelated work."),
            ("Choose the real consistency requirement", "For an expensive but repeatable read, accept bounded duplicate work and size the backing service for a burst. Add TTL jitter or prewarming where a synchronized expiry causes load spikes. For a correctness-critical mutation, a cache is the wrong lock; use a database uniqueness or transaction rule. [[spring/redis-cache-key-schema|Versioned keys]] and [[spring/cache-eviction|targeted eviction]] reduce wide clears."),
            ("Bound a clear", "A region clear can scan many keys. The default KEYS-based strategy can stall a large Redis keyspace; an SCAN-based batch strategy is available with a compatible driver, including Lettuce. Measure clear duration and Redis latency on realistic cardinality before using it in a request path. This lesson does not claim a measured cache-cluster result."),
        ],
        code='RedisCacheManager manager = RedisCacheManager.builder(\n        RedisCacheWriter.nonLockingRedisCacheWriter(connectionFactory))\n    .cacheDefaults(RedisCacheConfiguration.defaultCacheConfig()\n        .entryTtl(Duration.ofSeconds(47)))\n    .build();',
        cost="Duplicate loads scale with concurrent misses. A cache-wide writer lock trades that race for latency across unrelated keys; bulk clear cost grows with keyspace size and Redis scan behavior.",
        mistakes=["Do not treat sync=true as a distributed mutex across replicas.", "Do not use cache locks as a substitute for a database invariant.", "Do not run unmeasured region-wide clears on a large shared Redis instance."],
        related=["spring/cache-synchronized-loader", "spring/cache-eviction", "spring/redis-cache-key-schema", "spring/session-redis-replicas"],
    ),
    dict(
        slug="gateway-filter-ordering", section="spring/web-apis",
        title="Spring Cloud Gateway filter order: pre and post phases reverse",
        summary="Gateway combines global and route filters into one ordered chain; the first pre-filter is the last post-filter.",
        blocks=[
            ("Trace the same request twice", "A global trace filter with higher precedence runs before a route filter on the inbound path. When the downstream response returns, that trace filter runs after the route filter's post phase. That nesting matters when adding a request ID, rewriting headers, timing the downstream call, or translating an error. A filter that logs only before chain.filter(exchange) does not measure the whole route."),
            ("Separate edge identity from forwarded data", "A route may trust a user identity established at the gateway, but a downstream service must still have an authenticated contract for that identity. Remove client-supplied identity headers before setting gateway-owned values. [[spring/cloud-gateway-tenant|Tenant routing]] and [[spring/trusted-forwarded-headers|proxy headers]] have the same spoofing risk if the outer edge does not define which inputs it owns."),
            ("Verify execution order", "Give a test filter an ordered pre marker and a post marker, then assert the observed sequence around a route filter. Include a failed downstream call; post handling may still be needed for metrics and cleanup. Keep routing, authentication and observability concerns in distinct filters so their ordering can be reasoned about. The sketch uses the reactive Gateway server API."),
        ],
        code='public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {\n    long startedAt = System.nanoTime();\n    return chain.filter(exchange).doFinally(signal ->\n        routeTimer.record(System.nanoTime() - startedAt));\n}\npublic int getOrder() { return -47; }',
        cost="Each filter adds work to every routed request. Long-running or blocking work in a reactive filter occupies event-loop capacity; the timer itself should avoid blocking export.",
        mistakes=["Do not assume a low numeric order runs last in both phases.", "Do not trust a client-supplied tenant header after adding a gateway filter.", "Do not block inside a reactive Gateway filter to write logs or fetch policy."],
        related=["spring/cloud-gateway-tenant", "spring/trusted-forwarded-headers", "spring/gateway-authenticated-rate-limit", "spring/gateway-retry-body-budget"],
    ),
    dict(
        slug="gateway-authenticated-rate-limit", section="spring/security",
        title="Spring Cloud Gateway rate limits: derive the key from authenticated identity",
        summary="A Redis token bucket only isolates callers when its key resolver uses a trusted principal or tenant claim.",
        blocks=[
            ("The bucket needs an owner", "A rate limit on the public path /api/orders is global if every request resolves to the same key. A key taken from ?tenant= is attacker-controlled. For an authenticated API, derive the key from the verified principal or a validated tenant claim and include the route's policy name when limits differ. The built-in principal-name resolver is useful only when the selected security chain actually authenticates the request. [[spring/tenant-claim-required|Tenant claim validation]] must happen before bucket assignment."),
            ("Size the token bucket deliberately", "RedisRateLimiter uses replenishRate, burstCapacity and requestedTokens. A burst capacity of 47 with a replenish rate of 7 can admit a short spike and then recover roughly seven tokens per second, assuming one token per request. The defaults for empty keys deny requests; decide explicitly how anonymous endpoints are handled. A 429 should carry a client-facing retry policy, while [[spring/gateway-retry-body-budget|gateway retries]] must not multiply calls to a saturated downstream service."),
            ("Test identity and failure", "Send two authenticated principals and prove their buckets are separate. Then send a spoofed tenant header and verify it cannot change the key. Test Redis unavailability: whether the gateway fails closed or degrades is a product policy, not something to discover during an outage. The YAML sketch assumes a configured KeyResolver bean and reactive Redis dependency."),
        ],
        code='spring:\n  cloud:\n    gateway:\n      server:\n        webflux:\n          routes:\n            - id: order-api\n              uri: http://order-service\n              predicates:\n                - Path=/api/orders/**\n              filters:\n                - name: RequestRateLimiter\n                  args:\n                    key-resolver: "#{@verifiedTenantKeyResolver}"\n                    redis-rate-limiter.replenishRate: 7\n                    redis-rate-limiter.burstCapacity: 47',
        language="yaml",
        cost="Each admitted request checks Redis. A shared Redis outage can affect every protected route, while overly broad keys make unrelated users contend for one bucket.",
        mistakes=["Do not key a tenant bucket from a query parameter or unchecked header.", "Do not assume rate limiting replaces downstream admission control.", "Do not forget the empty-key and Redis-outage behaviors in tests."],
        related=["spring/cloud-gateway-tenant", "spring/tenant-claim-required", "spring/gateway-filter-ordering", "spring/gateway-retry-body-budget"],
    ),
    dict(
        slug="gateway-retry-body-budget", section="spring/web-apis",
        title="Spring Cloud Gateway retry: idempotency, buffered bodies and the byte budget",
        summary="Gateway retry can repeat downstream work and retain a request body; both costs need an explicit route policy.",
        blocks=[
            ("Retries change the command contract", "A timed-out POST may have committed an order even though the gateway never received its response. Blindly sending the body again can create a second order. The Gateway Retry filter defaults are centered on GET and selected 5xx or exception cases; enabling POST is an explicit decision. For writes, require a stable idempotency key and enforce it in the downstream database, as in [[spring/idempotent-receipt-post|the receipt command]]. A gateway header alone cannot guarantee once-only effects."),
            ("Bound retained bytes", "When a route retries a request that has a body, Gateway can cache that body to replay it. A 12 MiB upload multiplied by 47 concurrent attempts is already hundreds of MiB before other routing overhead. Put a RequestSize limit ahead of retry-sensitive routes, and prefer sending large uploads directly to a storage path with its own retry contract. [[spring/upload-byte-budget|Upload limits]] should be tested at the edge and application layers."),
            ("Exercise the uncertain result", "Make the downstream commit a write, then drop the response. The client should see a known uncertainty policy rather than an invisible duplicate. Check filter ordering with [[spring/gateway-filter-ordering|the combined chain]], because filters after Retry can run again. A test should cover retry count, body size rejection, timeout and a duplicate idempotency key."),
        ],
        code='- id: catalog-read\n  uri: http://catalog-service\n  predicates:\n    - Path=/api/catalog/**\n  filters:\n    - name: RequestSize\n      args:\n        maxSize: 2MB\n    - name: Retry\n      args:\n        retries: 2\n        methods: GET\n        statuses: BAD_GATEWAY,SERVICE_UNAVAILABLE',
        language="yaml",
        cost="Two retries can turn one request into three downstream attempts. Body replay retains bytes; backoff and client timeouts must fit one end-to-end latency budget.",
        mistakes=["Do not enable POST retry without downstream idempotency enforcement.", "Do not let a large body be replayed without a size limit.", "Do not mistake an upstream timeout for proof that no write committed."],
        related=["spring/idempotent-receipt-post", "spring/upload-byte-budget", "spring/gateway-filter-ordering", "spring/restclient-uncertain-commit"],
    ),
    dict(
        slug="stomp-handshake-identity", section="spring/security",
        title="Spring WebSocket STOMP identity: authenticate the handshake, authorize destinations",
        summary="STOMP CONNECT headers do not become trusted credentials just because a browser sends them over an upgraded connection.",
        blocks=[
            ("Identity comes from the HTTP entry", "A browser authenticates the WebSocket HTTP handshake. Spring associates the resulting Principal with the STOMP session; STOMP login and passcode headers are ignored by default for WebSocket authentication. A client-supplied userId header is still client input. The subscription and SEND destinations need message authorization, even after the handshake succeeds. [[spring/websocket-stomp-boundary|The STOMP boundary]] describes the endpoint and broker roles."),
            ("Separate subscription from command permission", "An operator may subscribe to /user/queue/receipts but must not SEND to a broker-owned /topic/stock route. Authorize inbound SEND and SUBSCRIBE message types and destination patterns through Spring Security's message authorization manager. A broker destination is not an application command. Bind tenant information to the authenticated principal and validate it again in the message handler; [[spring/tenant-claim-required|the tenant claim rule]] still applies."),
            ("Test the message channel", "Open a connection with no authenticated HTTP session and attempt CONNECT. Then authenticate, try an allowed private subscription and a forbidden broad topic. Assert the rejected frame never reaches the handler or broker. Browser origins and CSRF behavior also need an application test. The code is a configuration sketch, not a complete security chain."),
        ],
        code='messages\n    .simpDestMatchers("/app/receipts/**").hasAuthority("SCOPE_receipts.write")\n    .simpSubscribeDestMatchers("/user/queue/receipts").authenticated()\n    .simpSubscribeDestMatchers("/topic/admin/**").hasRole("ADMIN")\n    .anyMessage().denyAll();',
        cost="Authorization runs for inbound messages. That cost is small compared with allowing an unbounded SEND or SUBSCRIBE route; per-message database lookups should be measured and cached carefully.",
        mistakes=["Do not trust STOMP login/passcode or userId headers as verified identity.", "Do not authorize CONNECT and leave SEND or SUBSCRIBE destinations open.", "Do not let clients SEND directly to broker-owned notification topics."],
        related=["spring/websocket-stomp-boundary", "spring/tenant-claim-required", "spring/stomp-slow-client-budget", "spring/stomp-broker-scale-boundary"],
    ),
    dict(
        slug="stomp-slow-client-budget", section="spring/web-apis",
        title="Spring STOMP slow clients: send buffer and message-size limits",
        summary="A client that reads slowly can hold outbound messages in memory; the transport needs explicit time, buffer and inbound-size limits.",
        blocks=[
            ("The socket is not an infinite queue", "A warehouse dashboard can disconnect while the server is broadcasting frequent stock events. Until that connection is closed, outbound frames can accumulate. Spring's WebSocket transport supports a send-time limit and a send-buffer-size limit; when the send limit is exceeded, the session is closed. The inbound message-size limit protects the application from oversized STOMP payloads, but it does not replace HTTP handshake controls."),
            ("Set a product policy", "If the dashboard only needs the latest stock total, publishing every intermediate event is wasteful. Coalesce by SKU or send a compact invalidation and let the client refetch. A bounded message stream and reconnect snapshot are more predictable than trying to buffer an hour of updates. [[spring/stomp-broker-scale-boundary|Broker choice]] affects where messages queue, while [[spring/async-admission-and-completion|admission control]] applies to producers."),
            ("Load-test a deliberately stalled reader", "Open one client that stops consuming, keep several healthy clients, and publish at the expected peak rate. Verify the stalled session is closed without delaying healthy recipients or exhausting heap. Inspect transport counters, connection count and oldest pending frame age. The example values are a planning start, not a measured safe setting for this deployment."),
        ],
        code='@Override\npublic void configureWebSocketTransport(WebSocketTransportRegistration transport) {\n    transport.setSendTimeLimit(8_000);\n    transport.setSendBufferSizeLimit(512 * 1024);\n    transport.setMessageSizeLimit(64 * 1024);\n}',
        cost="The buffer cap bounds retained bytes per slow session; total memory still scales with concurrent sessions. A low cap can disconnect clients on transient network stalls, so measure production-shaped traffic.",
        mistakes=["Do not interpret a successful send call as proof the browser consumed the frame.", "Do not increase buffers without multiplying the limit by expected connection count.", "Do not use transport limits as a substitute for an event retention or replay policy."],
        related=["spring/websocket-stomp-boundary", "spring/stomp-handshake-identity", "spring/stomp-broker-scale-boundary", "spring/async-admission-and-completion"],
    ),
    dict(
        slug="stomp-broker-scale-boundary", section="spring/web-apis",
        title="Spring STOMP simple broker versus relay: the multi-instance boundary",
        summary="The simple broker stores subscriptions in one application process; a shared broker relay changes routing and failure ownership.",
        blocks=[
            ("A local subscription has a location", "With the simple broker, instance A knows its own connected subscribers. If an HTTP request lands on instance B and B broadcasts an event, B cannot assume A's clients receive it. Sticky routing may hide this in a test but fails when a connection moves or an instance dies. A broker relay forwards messages to an external STOMP broker, giving multiple application instances a shared route; it also creates a broker dependency that needs health and reconnect policies."),
            ("Separate live delivery from durable history", "Neither a WebSocket connection nor a broker relay means an offline browser will later receive missed stock events. Keep durable events or current state in a store and send a snapshot after reconnect. [[spring/session-redis-replicas|Shared HTTP session state]] does not share the simple broker's subscription table. [[spring/stomp-slow-client-budget|Slow-client limits]] still apply at the WebSocket edge even when the broker is external."),
            ("Prove cross-node delivery", "Attach a subscriber to instance A, publish through instance B, then restart A and reconnect the browser. Assert an authorized subscriber receives the live event and a snapshot restores missed state. Add a broker outage case. The relay snippet is only the application-side configuration; broker credentials, destinations and capacity require a deployment test."),
        ],
        code='registry.enableStompBrokerRelay("/topic", "/queue")\n    .setRelayHost("broker.internal")\n    .setRelayPort(61613);\nregistry.setApplicationDestinationPrefixes("/app");',
        cost="A relay adds network hops and broker operations but lets separate app instances route to the same subscription space. Durability requires a distinct persistence design.",
        mistakes=["Do not assume the simple broker shares subscriptions between replicas.", "Do not call a live STOMP frame a durable notification.", "Do not skip a broker-outage and reconnect test when moving to a relay."],
        related=["spring/websocket-stomp-boundary", "spring/stomp-handshake-identity", "spring/stomp-slow-client-budget", "spring/session-redis-replicas"],
    ),
    dict(
        slug="http-service-client-contract", section="spring/web-apis",
        title="Spring HTTP service client: the interface is a contract, not a transport policy",
        summary="An @HttpExchange interface declares remote requests; its RestClient adapter still needs a base URL, timeouts and error policy.",
        blocks=[
            ("Keep the interface narrow", "A pricing client can expose one quote lookup through @GetExchange and map the path parameter explicitly. HttpServiceProxyFactory creates a typed proxy backed by a RestClient adapter. That removes handwritten request assembly, but the underlying RestClient still decides connection and read timeouts, authentication, status handling and observability. [[spring/restclient-request-factory|The request factory]] is where much of the actual I/O behavior is chosen."),
            ("Define failure as part of the call", "A 404 may mean a product is absent; a 503 may mean the pricing service is unavailable. Do not collapse both into null. Convert known status responses into typed application failures and pass an end-to-end deadline from the caller. [[spring/restclient-timeout-budget|Timeout budgeting]] and [[spring/restclient-status-no-retry|status retry rules]] should be reviewed beside the interface, even though they live in separate configuration."),
            ("Test the HTTP wire", "Point the proxy at a stub server and verify the URL, encoded path variable, required headers and result mapping. Return a malformed body and a 503 in separate cases. A mocked Java interface call proves neither serialization nor error translation. The code is an integration sketch; add the project's auth interceptor and error handler before production use."),
        ],
        code='@HttpExchange("/v1/prices")\ninterface PricingClient {\n    @GetExchange("/{sku}")\n    PriceQuote quote(@PathVariable String sku);\n}\nRestClient restClient = RestClient.builder()\n    .baseUrl("https://pricing.internal")\n    .build();\nPricingClient client = HttpServiceProxyFactory\n    .builderFor(RestClientAdapter.create(restClient)).build()\n    .createClient(PricingClient.class);',
        cost="The proxy adds small dispatch overhead; network latency, connection pooling, body size and retries dominate. An unbounded read can hold a request thread and pooled connection.",
        mistakes=["Do not mistake a typed interface for configured timeouts or status mapping.", "Do not test only the Java method signature and call it an HTTP integration test.", "Do not hide remote 404 and 503 responses behind the same null result."],
        related=["spring/restclient-request-factory", "spring/restclient-timeout-budget", "spring/restclient-status-no-retry", "spring/http-service-client-retry-boundary"],
    ),
    dict(
        slug="http-service-client-retry-boundary", section="spring/web-apis",
        title="Spring HTTP service client retries: an interface cannot prove the server did not commit",
        summary="A proxy call that times out after sending a write has an uncertain outcome; retries belong to the operation contract.",
        blocks=[
            ("A timeout is an observation", "The client sends a stock adjustment, waits, and times out. The upstream service may have committed before the response was lost. Wrapping an @HttpExchange method in a generic retry can issue the adjustment again. That risk is identical to handwritten RestClient code; the proxy does not change HTTP semantics. [[spring/restclient-uncertain-commit|The uncertain-commit boundary]] applies to every client style."),
            ("Separate safe reads and protected writes", "A bounded retry for an idempotent GET can recover from a transient connection failure if its total delay fits the caller's deadline. A POST needs a server-enforced idempotency key or a reconciliation endpoint, and only the server can enforce one logical outcome. Keep the key stable across attempts. [[spring/idempotent-receipt-post|The receipt flow]] shows the database uniqueness rule behind that promise."),
            ("Test the lost-response window", "Make the stub accept the first POST and drop its response. Assert the second attempt carries the same key, then test against the real service's idempotency table to prove one stored command. Also test exhausted retry budget and 4xx rejection. The snippet names the request header; it does not implement server deduplication or claim exactly-once delivery."),
        ],
        code='@HttpExchange("/v1/stock")\ninterface StockClient {\n    @PostExchange("/adjustments")\n    AdjustmentReceipt adjust(\n        @RequestHeader("Idempotency-Key") String commandId,\n        @RequestBody StockAdjustment adjustment);\n}',
        cost="Retries multiply downstream load and can extend tail latency. An idempotency table adds a write and retention policy, but prevents a duplicate business mutation after a lost response.",
        mistakes=["Do not infer rollback from a client timeout.", "Do not generate a new idempotency key for each attempt.", "Do not apply the same retry rule to reads and non-idempotent commands."],
        related=["spring/http-service-client-contract", "spring/restclient-uncertain-commit", "spring/restclient-idempotent-retry", "spring/idempotent-receipt-post"],
    ),
    dict(
        slug="testcontainers-service-connection-lifecycle", section="spring/testing",
        title="Spring Boot Testcontainers: service connections and cached-context lifecycle",
        summary="@ServiceConnection supplies connection details, but a test-scoped container can stop while a cached Spring context still points to it.",
        blocks=[
            ("Connection details win over a hand-built URL", "Spring Boot can inspect a Testcontainers container marked @ServiceConnection and supply the matching connection details to auto-configuration. That removes hard-coded random ports from a repository test. The container must still be in the test classpath and supported by the relevant Spring Boot integration. If several data sources exist, qualify which connection is under test instead of hoping a generic container bean selects the right one."),
            ("Align two lifetimes", "A static JUnit container managed by the Testcontainers extension can stop after its test class. Spring's test context cache may retain an ApplicationContext that points to that stopped database for a later class. Put the container under Spring context management when sharing the context, or deliberately avoid context reuse; do not solve a lifecycle mismatch by adding sleeps. [[spring/context-testing|Context tests]] and [[spring/boot-config-process-test-boundary|process-boundary tests]] have different costs."),
            ("Prove reuse across classes", "Run two test classes sequentially with the same cached context. Assert both can query the database and that the mapped port remains valid. Then run them in parallel if CI does so. The bean sketch states ownership by Spring; dependency coordinates, image policy and test database migrations remain project-specific."),
        ],
        code='@TestConfiguration(proxyBeanMethods = false)\nclass InventoryDatabaseTestConfig {\n    @Bean\n    @ServiceConnection\n    PostgreSQLContainer<?> inventoryDatabase() {\n        return new PostgreSQLContainer<>("postgres:16-alpine");\n    }\n}',
        cost="Starting a real database container is slower than a mocked repository, but it checks driver, schema and transaction behavior. Context reuse saves startup time only when the container lifetime matches it.",
        mistakes=["Do not assume @ServiceConnection proves migrations or application queries work.", "Do not let a JUnit-scoped container stop before a reused Spring context.", "Do not replace database integration tests with an in-memory dialect when SQL behavior matters."],
        related=["spring/context-testing", "spring/testing-boundaries", "spring/boot-config-process-test-boundary", "spring/kafka-testing-layers"],
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
    body = "<p>" + paragraph(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + paragraph(content) + "</p>"
    body += ('<h2>Implementation sketch</h2><pre><code class="language-' + item.get("language", "java")
             + '">' + html.escape(item["code"], quote=False) + "</code></pre>")
    body += "<h2>Cost and verification</h2><p>" + paragraph(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(
        "<li>" + paragraph(mistake) + "</li>" for mistake in item["mistakes"]
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
        sort_order=4900 + number, published_at=stamp, created_at=stamp, updated_at=stamp,
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
    "spring/production": "Redis cache expiry and shared-writer behavior",
    "spring/web-apis": "Gateway, WebSocket and HTTP client boundaries",
    "spring/security": "Gateway and STOMP identity boundaries",
    "spring/testing": "Testcontainers connection lifecycle",
}
for section, heading in headings.items():
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({
        "title": heading,
        "summary": "Follow one operation through its failure path and linked application boundary.",
        "lessons": paths,
    })
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["spring/spring-boot"]
parent["body"] += "<h2>Edge and cache operation contracts</h2><ul>" + "".join(
    '<li><a href="/spring/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons
) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("spring/cache-keys", "spring/redis-cache-key-schema"),
    ("spring/cache-eviction", "spring/redis-cache-writer-races"),
    ("spring/cloud-gateway-tenant", "spring/gateway-authenticated-rate-limit"),
    ("spring/websocket-stomp-boundary", "spring/stomp-handshake-identity"),
    ("spring/restclient-request-factory", "spring/http-service-client-contract"),
    ("spring/context-testing", "spring/testcontainers-service-connection-lifecycle"),
]:
    row = by_path[source]
    row["body"] += ('<h2>Related boundary</h2><p><a href="/' + target + '">'
                    + html.escape(titles[target]) + "</a></p>")
    row["updated_at"] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring articles; new total", sum(
    row["path"].startswith("spring/") and row["type"] == "article" for row in rows
))

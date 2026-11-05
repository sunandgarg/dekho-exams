"""Add original Spring production-boundary lessons to local preview fixtures."""

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
        slug="actuator-management-port-boundary",
        title="Spring Actuator management port: separate listener, explicit access rule",
        summary="Move operational endpoints to a separate listener when the network needs it, then secure that listener as a distinct entry point.",
        blocks=[
            ("A port is a routing boundary", "A receipt API serves customers on one listener while an operations network reaches a second. Setting management.server.port gives Actuator its own HTTP listener; management.server.address can bind that listener to an internal interface. Neither property authenticates callers. The network must restrict reachability, and the application must still decide which principals may inspect or change operations state. [[spring/security-filter-chain|Security chains]] and [[spring/actuator-health|health checks]] have separate jobs."),
            ("Review the security back-off", "An application-defined SecurityFilterChain takes control of HTTP access rules. Do not assume Spring Boot will add a protective Actuator rule after that point. Give management requests an explicit matcher and authorization policy, and test it through the actual listener. A reverse proxy that forwards the management port onto the public host can undo the intended isolation. Prefer a narrow exposure list even behind a firewall."),
            ("Test the deployment path", "Probe the application listener and management listener independently from an allowed operations host and a denied client host. Confirm an unauthenticated caller cannot reach a sensitive endpoint, even if the network rule is accidentally widened. Include a startup test for conflicting port and address settings, and verify service discovery does not advertise the management listener as a customer API. [[spring/dependency-readiness|Readiness]] may need a deliberate exception for the platform probe."),
        ],
        code="management.server.port=9471\nmanagement.server.address=${MANAGEMENT_BIND_ADDRESS:127.0.0.1}\nmanagement.endpoints.web.exposure.include=health,info,prometheus",
        language="properties",
        cost="A second listener consumes a small amount of memory and one port allocation. The main operational cost is maintaining two routing and access paths; every endpoint added to exposure expands what that path can reveal or change.",
        mistakes=["Do not treat a separate port as authentication.", "Do not define a custom SecurityFilterChain and assume Actuator access remains automatically protected.", "Do not publish the management listener through the same public ingress without reviewing its route and credentials."],
        related=["spring/security-filter-chain", "spring/actuator-health", "spring/dependency-readiness", "spring/actuator-prometheus-scrape-contract", "spring/actuator-runtime-logger-control"],
    ),
    dict(
        slug="actuator-prometheus-scrape-contract",
        title="Spring Prometheus scrape endpoint: registry, exposure and label contract",
        summary="A metrics scrape needs the registry, an exposed endpoint and stable labels; the diagnostic metrics endpoint is a different interface.",
        blocks=[
            ("Three pieces must agree", "Adding Actuator alone does not make a Prometheus scrape. Include the Prometheus registry in the application, expose the prometheus endpoint over HTTP, and configure the collector to reach the instance through an allowed operations route. The scrape representation lives at the Actuator prometheus endpoint; [[spring/metric-cardinality|metric-cardinality]] starts with what each meter labels. The Actuator metrics endpoint is useful for human inspection, but it is not the collector's scrape format."),
            ("Keep identity stable", "A request counter tagged with customer ID creates one series per customer, which grows with traffic rather than with the small set of routes and outcomes. Tag by bounded route template, method and response class. Keep environment and service identity consistent across redeployments; do not put timestamps or pod IDs into a custom label when the collector already supplies target identity. A collector outage should not make the receipt API fail a request."),
            ("Check real samples", "After deployment, fetch the scrape from the same network and credentials used by the collector. Assert that the receipt outcome counter is present after one success and one rejection, then inspect its distinct label combinations. A zero or missing series can mean no event occurred, a bean was not registered, the registry is absent, or the endpoint is not exposed. These are different faults and deserve different tests. [[spring/actuator-management-port-boundary|Management routing]] determines where the collector connects."),
        ],
        code="management.endpoints.web.exposure.include=health,prometheus\nmanagement.metrics.tags.application=receipt-api",
        language="properties",
        cost="Scraping walks and formats the registered meters on each interval. Series cost grows roughly with the product of distinct label values; keep that product bounded before choosing a short scrape interval.",
        mistakes=["Do not point a Prometheus collector at the diagnostic metrics endpoint.", "Do not expose a scrape publicly just because it contains no customer response bodies.", "Do not use receipt IDs, tenant IDs or request IDs as metric label values."],
        related=["spring/metric-cardinality", "spring/actuator-management-port-boundary", "spring/actuator-health", "spring/boot-trace-client-builder", "spring/tracing-log-correlation"],
    ),
    dict(
        slug="actuator-health-details-exposure",
        title="Spring health details: status for probes, diagnostics for operators",
        summary="Return a small status to routine probes while limiting component names and failure details to authorized operators.",
        blocks=[
            ("Health has two audiences", "A scheduler wants a quick answer about whether a receipt instance can receive traffic. An operator may need to know which contributor is failing. A public probe response should not casually disclose database names, broker topology or exception text. The health show-details and show-components settings control how much information the endpoint returns; an authorization rule still determines who can call it. [[spring/dependency-readiness|Readiness]] answers admission to traffic, while [[spring/actuator-health|health design]] decides what each indicator measures."),
            ("Separate failure domains", "Do not make liveness depend on a remote payment processor. A temporary remote outage is not proof that restarting the JVM will help, and a restart loop can amplify the outage. A readiness group may include a dependency if this instance truly cannot serve any request without it, but that decision can remove all instances at once during a shared failure. Put nonessential dependency signals in an operator-facing diagnostic group."),
            ("Verify both views", "Call the probe path without credentials and inspect the exact response body. Then call the operator path with and without the permitted role. Assert that unauthorized output omits contributor details and that the authorized view identifies a forced failing contributor. Run the check behind the real proxy because path rewriting and separate management ports alter which rule sees the request. Keep indicator work bounded so a stalled dependency cannot occupy every probe worker."),
        ],
        code="management.endpoint.health.show-details=when-authorized\nmanagement.endpoint.health.show-components=when-authorized\nmanagement.endpoint.health.roles=OPS",
        language="properties",
        cost="More health contributors add probe latency and may consume connection-pool slots. A deeply detailed response also increases the information exposed to anyone who can call that endpoint; cache or bound expensive diagnostics separately.",
        mistakes=["Do not expose all health details to a public load balancer probe.", "Do not add every remote dependency to liveness.", "Do not assume a role setting replaces an explicit request authorization policy."],
        related=["spring/actuator-health", "spring/dependency-readiness", "spring/actuator-management-port-boundary", "spring/actuator-prometheus-scrape-contract", "spring/security-filter-chain"],
    ),
    dict(
        slug="cache-after-commit-visibility",
        title="Spring cache after commit: keep rolled-back writes out of readers",
        summary="Publish cache invalidation after the database commits so a failed transaction cannot leave readers with an impossible state.",
        blocks=[
            ("The database decides first", "A receipt update can pass validation, write a row and still roll back when a later constraint fails. Updating a shared cache inside that transaction lets another request observe a value the database never committed. An after-commit event moves invalidation to the success side of the boundary. [[spring/cache-eviction|Eviction]] then makes the next read load durable state. The event handler below is short and deliberately does not contact another service."),
            ("Know the remaining gap", "After-commit work runs in the same process and can be lost if the process stops between commit and eviction. Give entries a bounded TTL, and use a durable change record when strict cross-node invalidation is required. A transaction-aware cache decorator can defer ordinary put, evict and clear operations until commit, but immediate atomic operations such as putIfAbsent have different timing. Read the behavior of the chosen CacheManager rather than assuming every cache action is deferred."),
            ("Test two timelines", "First commit a receipt edit and verify that a subsequent reader sees the new stored value. Then force a rollback after the edit and verify no invalidation event ran. Exercise a node restart just after commit: TTL should eventually repair the stale entry, while a durable relay is needed for a tighter freshness guarantee. [[spring/transaction-events|Transaction events]] and [[spring/outbox-relay-state-machine|an outbox relay]] define those different delivery promises."),
        ],
        code="@Component\nfinal class ReceiptCacheInvalidator {\n    private final CacheManager cacheManager;\n\n    ReceiptCacheInvalidator(CacheManager cacheManager) {\n        this.cacheManager = cacheManager;\n    }\n\n    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)\n    void on(ReceiptChanged changed) {\n        Cache receiptCache = cacheManager.getCache(\"receipt-view-v3\");\n        if (receiptCache != null) receiptCache.evict(changed.cacheKey());\n    }\n}",
        cost="An invalidation adds one cache write after each committed edit and the next read pays a cache miss. A durable relay adds storage and retry work, but closes the process-crash gap that an in-memory event cannot close.",
        mistakes=["Do not populate shared cache state from a transaction that may roll back.", "Do not assume an after-commit in-memory handler is durable across process failure.", "Do not assume every atomic cache operation waits until commit."],
        related=["spring/cache-eviction", "spring/transaction-events", "spring/outbox-relay-state-machine", "spring/cache-null-result-policy", "spring/redis-cache-ttl-vs-tti"],
    ),
    dict(
        slug="cache-null-result-policy",
        title="Spring null-result caching: decide whether a miss should survive",
        summary="A missing record can be deliberately uncached or cached briefly; either choice changes load and freshness after creation.",
        blocks=[
            ("A miss is an outcome", "A receipt may be absent because it was never created, because replication has not caught up, or because the caller cannot see it. These cases should not automatically share one cache key or retention policy. With @Cacheable, an unless expression can veto storage after the method returns; the example does not cache null. [[spring/cache-keys|Tenant-aware keys]] prevent one tenant's miss from masking another tenant's receipt. Do not encode authorization failure as a cached absence."),
            ("Choose the load tradeoff", "Never caching misses preserves immediate visibility when a receipt is created, but repeated requests for unknown IDs all reach the database. A short negative cache can protect the database under repeated bad lookups, but a newly created record remains invisible until invalidation or expiry. If the result type is Optional, Spring evaluates #result against its contained value, so an empty Optional is still a null business result for this expression. Check what the selected provider stores when nulls are allowed."),
            ("Exercise creation after absence", "Query an absent receipt, create it, and query again through the same API. With a no-null policy, the second read should reach storage and return it. For negative caching, add an explicit create-time invalidation and assert its behavior across nodes and rollback. Count misses by bounded route and outcome, never by receipt ID. [[spring/cache-after-commit-visibility|Commit timing]] matters for that invalidation, and [[spring/redis-cache-ttl-vs-tti|expiry]] limits the damage when a signal is lost."),
        ],
        code="@Cacheable(cacheNames = \"receipt-view-v3\",\n           key = \"#p0 + ':' + #p1\",\n           unless = \"#result == null\")\npublic ReceiptView findVisibleReceipt(String tenantId, String receiptId) {\n    return receipts.findVisible(tenantId, receiptId).orElse(null);\n}",
        cost="Skipping null storage increases repeated database work for missing IDs. Negative caching reduces that work but spends capacity on misses and adds a freshness window that must be accepted by the product contract.",
        mistakes=["Do not share a missing-result key across tenants or authorization scopes.", "Do not cache an empty result indefinitely when the record may be created later.", "Do not use a null cache entry to hide an authorization failure."],
        related=["spring/cache-keys", "spring/cache-after-commit-visibility", "spring/redis-cache-ttl-vs-tti", "spring/cache-eviction", "spring/cache-synchronized-loader"],
    ),
    dict(
        slug="redis-cache-serialization-rollout",
        title="Spring Redis cache serialization: roll payload formats without mixed readers",
        summary="Version the cache namespace before a payload or serializer change so old values are never decoded under a new contract.",
        blocks=[
            ("Cache entries have a wire format", "A receipt view stored in Redis is bytes, not a Java object shared in memory. A serializer change, renamed field or new application version can make an existing entry unreadable. Treat the cache name and prefix as a format boundary: write the new view under receipt-view-v4 while old nodes continue using receipt-view-v3. [[spring/redis-cache-key-schema|Key schemas]] cover tenant and identifier separation; the version covers payload interpretation."),
            ("Roll forward in stages", "Deploy code that can read its new namespace and refill it from the database. Keep the old namespace until old nodes leave traffic, then let its TTL retire entries. Do not mass-delete a shared Redis instance just to clear one application cache. Pin the serializer in configuration, test real encoded bytes from the previous release, and reject permissive polymorphic decoding of untrusted values. If two versions must share keys, use a deliberately backward-compatible envelope and a migration test instead of hope."),
            ("Measure the cold interval", "A new namespace produces a temporary cache-miss wave. Stage rollout capacity, rate-limit expensive rebuilds and record miss ratio by bounded cache name. Test an old payload, a new payload, a corrupted value and an entry written by a node mid-rollout. A corrupt cache entry should not silently become a wrong receipt; classify and evict it or fail the request according to the data contract. [[spring/cache-after-commit-visibility|Commit-safe invalidation]] remains necessary after writes."),
        ],
        code="spring.cache.cache-names=receipt-view-v4\nspring.cache.redis.time-to-live=47m\nspring.cache.redis.use-key-prefix=true\nspring.cache.redis.key-prefix=receipt-api:",
        language="properties",
        cost="A version change temporarily duplicates old and new entries and increases database reads while the new cache warms. TTL bounds the old storage footprint; coordinated deployment and targeted metrics bound the cold-cache load.",
        mistakes=["Do not change a serializer while leaving old and new nodes on the same undecorated cache keys.", "Do not clear an entire shared Redis database to retire one payload format.", "Do not permit broad untrusted type deserialization merely to read legacy entries."],
        related=["spring/redis-cache-key-schema", "spring/redis-cache-ttl-vs-tti", "spring/cache-after-commit-visibility", "spring/cache-keys", "spring/metric-cardinality"],
    ),
    dict(
        slug="tracing-log-correlation",
        title="Spring tracing and logs: preserve request identity across outbound calls",
        summary="Correlate logs with trace and span IDs while using instrumented client builders for outbound propagation.",
        blocks=[
            ("Correlation is a path, not a tag dump", "A receipt request may pass through an API, a pricing service and a worker. With tracing enabled, the logging context can carry trace and span identifiers so an operator can join a log line to the request path. Those identifiers are not a substitute for a stable business receipt ID in an audit record, and the receipt ID should not become a high-cardinality metric label. [[spring/metric-cardinality|Metrics labels]] and [[spring/async-trace-context|async trace handoff]] require their own controls."),
            ("Use managed builders", "Spring Boot customizes its injected RestClient.Builder and WebClient.Builder for observation and trace propagation when the required instrumentation is present. Constructing a raw client outside that path may omit propagation, even if incoming requests have trace IDs. The example accepts the managed builder and a configured service base address. Avoid printing authorization headers or customer payloads to compensate for missing trace context; repair the client path instead."),
            ("Check a complete hop", "Send one request with a test trace context, capture logs on both services and verify the same trace ID appears on the inbound and outbound sides while span IDs differ where work is nested. Repeat through a queued task: a thread-local context may be absent unless the executor captures it. Sampling means an unsampled request can still have correlation identifiers but no stored trace; logs must remain useful without assuming every trace is retained. [[spring/boot-trace-client-builder|Client builder wiring]] is the companion implementation lesson."),
        ],
        code="@Bean\nRestClient receiptPartnerClient(\n        RestClient.Builder managedBuilder,\n        @Value(\"${receipt.partner-base}\") String partnerBase) {\n    return managedBuilder.baseUrl(partnerBase).build();\n}",
        cost="Trace propagation adds small headers and context work per call; collecting and retaining spans costs more. Sample by an explicit policy, and keep log fields bounded so correlation does not become an uncontrolled data-export path.",
        mistakes=["Do not construct a raw HTTP client and assume it received Boot's trace customization.", "Do not use customer IDs, tokens or payloads as trace tags or log correlation fields.", "Do not treat a missing stored span as proof that the request never happened."],
        related=["spring/boot-trace-client-builder", "spring/async-trace-context", "spring/metric-cardinality", "spring/actuator-prometheus-scrape-contract", "spring/actuator-management-port-boundary"],
    ),
    dict(
        slug="actuator-runtime-logger-control",
        title="Spring Actuator loggers endpoint: temporary diagnosis with guarded write access",
        summary="Runtime log-level changes can help diagnose a narrow fault, but the endpoint is a privileged write interface.",
        blocks=[
            ("Viewing and changing are different powers", "The loggers endpoint reports configured and effective levels and can accept a write for a named logger. That write can suddenly emit large volumes of sensitive application detail. Expose the endpoint only through the operations route, require a role authorized to change configuration, and record who made the change outside the application log level being modified. [[spring/actuator-management-port-boundary|A management listener]] narrows network reach but does not supply authorization."),
            ("Scope the intervention", "Raise logging for the smallest package involved in a receipt failure, set a short investigation window, and restore the previous level. Changing the root logger to DEBUG under production load can bury the signal, exhaust log transport and include request headers if existing code logs them. A runtime level change need not survive restart; use reviewed configuration for a permanent setting. Prefer [[spring/tracing-log-correlation|trace correlation]] to broad debug output when following one request."),
            ("Verify denial and rollback", "From an unprivileged account, test both read and write requests to the endpoint. From the operations role, change one named logger, confirm its effective level, then restore the prior configured level and confirm normal volume returns. Exercise a restart and check that the intended baseline wins. Keep an operational record of the affected service, instance, logger, actor and expiration time without logging credentials or payloads."),
        ],
        code="management.endpoints.web.exposure.include=health,loggers\nlogging.level.com.aitrove.receipts=INFO",
        language="properties",
        cost="The endpoint itself is cheap when idle. A broad DEBUG setting can multiply log bytes, CPU formatting work and downstream storage charges; bound the logger and duration before enabling it.",
        mistakes=["Do not grant runtime logger writes to every authenticated user.", "Do not change the root logger for a narrow production issue.", "Do not assume a runtime change is a permanent configuration update."],
        related=["spring/actuator-management-port-boundary", "spring/actuator-health-details-exposure", "spring/tracing-log-correlation", "spring/security-filter-chain", "spring/metric-cardinality"],
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
    body += ('<h2>Implementation contract</h2><pre><code class="language-' + item.get("language", "java") + '">'
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
        subject="spring-production", tags=["spring", "spring-boot", "production", item["slug"]],
        sort_order=5800 + number, published_at=stamp, created_at=stamp, updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": "spring/production",
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7 where relevant",
        "java_version": "21 or later",
        "verification_suite": "Spring API contract review; snippets require an application-specific model",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

paths = ["spring/" + item["slug"] for item in lessons]
hub = by_path["spring/production"]
hub["data"]["modules"].append({
    "title": "Management, observability and cache visibility",
    "summary": "Operational access, scrape contracts, trace propagation and cache rollout behavior.",
    "lessons": paths,
})
for section in ("spring/production", "spring/spring-boot"):
    entry = by_path[section]
    entry["body"] += "<h2>Management and cache contracts</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    entry["updated_at"] = stamp

for source, target in [
    ("spring/actuator-health", "spring/actuator-health-details-exposure"),
    ("spring/metric-cardinality", "spring/actuator-prometheus-scrape-contract"),
    ("spring/dependency-readiness", "spring/actuator-management-port-boundary"),
    ("spring/cache-eviction", "spring/cache-after-commit-visibility"),
    ("spring/cache-keys", "spring/cache-null-result-policy"),
    ("spring/redis-cache-key-schema", "spring/redis-cache-serialization-rollout"),
    ("spring/boot-trace-client-builder", "spring/tracing-log-correlation"),
    ("spring/security-filter-chain", "spring/actuator-runtime-logger-control"),
]:
    entry = by_path[source]
    entry["body"] += ('<h2>Related production contract</h2><p><a href="/' + target + '">'
                      + html.escape(titles[target]) + "</a>.</p>")
    entry["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(lessons)} Spring production lessons; {len(rows)} total fixture records")

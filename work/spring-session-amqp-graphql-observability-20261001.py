"""Expand Spring session, AMQP, GraphQL and observability boundaries."""

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
        slug="session-redis-replicas", section="spring/security", subject="spring-security",
        title="Spring Session Redis across replicas: shared login state has a Redis failure boundary",
        summary="Spring Session replaces container-local HttpSession storage with Redis-backed state so a browser request can reach any application replica.",
        blocks=[
            ("Move the state, not the cookie", "A parcel operator signs in through replica A, then a load balancer sends the next request to replica B. With a container-local session, B knows only the cookie ID and cannot load its state. Spring Session's Redis repository lets both replicas resolve the same ID. The browser still sends a cookie; the server stores the session contents in Redis. [[spring/oauth2-login-session|OAuth2 login]] may store authorization state in that session, so an unavailable Redis tier can make login or subsequent authenticated requests fail."),
            ("Set a failure policy", "Choose a session timeout, Redis namespace and connection budget for this application. Keep the stored attributes small and serialization-compatible across rolling releases; placing a large mutable domain graph in a session amplifies every read or write. Redis eviction can remove an active session before its intended idle timeout, so reserve capacity and set an eviction policy compatible with login state. This configuration sketch does not provide Redis failover or guarantee session availability."),
            ("Test the route change", "Authenticate, pin the first request to one replica, send the next request with the same cookie to another, then disconnect Redis. Record whether the application returns an authentication failure or a service error; make that behavior explicit in the client flow. A single-node login test cannot prove cross-replica session continuity."),
        ],
        code='server:\n  servlet:\n    session:\n      timeout: 23m\nspring:\n  session:\n    redis:\n      namespace: parcel-console:session\n  data:\n    redis:\n      host: redis.internal', language="yaml",
        cost="Each session lookup adds Redis I/O and serialized state. Size the pool for peak authenticated traffic and measure Redis latency separately from controller latency.",
        mistakes=["Do not assume a shared cookie makes container-local sessions shared.", "Do not put large entity graphs or nonportable serialized classes in session attributes.", "Do not treat Redis as optional when session lookup is on every authenticated path."],
        related=["spring/session-csrf-boundary", "spring/oauth2-login-session", "spring/boot-graceful-shutdown", "spring/session-cookie-policy"],
    ),
    dict(
        slug="session-cookie-policy", section="spring/security", subject="spring-security",
        title="Spring Session cookie policy: SameSite, Secure and the reverse proxy",
        summary="A shared session repository does not set the browser's cookie policy; the cookie still determines when a session ID crosses requests.",
        blocks=[
            ("Treat the cookie as a bearer credential", "Anyone holding the parcel-console session ID may act as its owner until the server rejects it. Set Secure on HTTPS deployments, HttpOnly to block script reads, and a SameSite policy that fits the login flow. A host-only cookie usually has a smaller exposure surface than a cookie shared with every subdomain. [[spring/session-csrf-boundary|CSRF protection]] remains relevant when a browser sends the cookie automatically."),
            ("Account for proxy termination", "If TLS ends at a trusted reverse proxy, the app may observe an internal HTTP hop. Configure forwarded-header handling only for headers supplied by that proxy, then verify the outgoing Set-Cookie contains Secure. Trusting arbitrary forwarded headers can let a client influence scheme and host decisions. [[spring/trusted-forwarded-headers|The forwarding boundary]] and [[spring/session-fixation-login|session rotation after login]] deserve a combined test."),
            ("Exercise the browser path", "Sign in through the public HTTPS origin, inspect the cookie attributes, make a cross-site POST, and verify the session is rotated after authentication. Test a callback from the configured identity provider separately: an overstrict SameSite choice may break the intended redirect flow. The serializer sketch fixes policy for one deployment; domain and path must match the actual public origin."),
        ],
        code='@Bean\nDefaultCookieSerializer parcelSessionCookie() {\n    DefaultCookieSerializer cookie = new DefaultCookieSerializer();\n    cookie.setCookieName("PARCEL_SESSION");\n    cookie.setUseSecureCookie(true);\n    cookie.setUseHttpOnlyCookie(true);\n    cookie.setSameSite("Lax");\n    return cookie;\n}',
        cost="Cookie flags have negligible server cost. A broad domain or long lifetime increases exposure if a session ID leaks; shorter idle time increases login frequency.",
        mistakes=["Do not set SameSite to None without requiring Secure and testing the actual browser flow.", "Do not derive cookie security from an untrusted forwarded scheme.", "Do not confuse HttpOnly with CSRF protection."],
        related=["spring/session-redis-replicas", "spring/session-csrf-boundary", "spring/trusted-forwarded-headers", "spring/session-fixation-login"],
    ),
    dict(
        slug="session-principal-invalidation", section="spring/security", subject="spring-security",
        title="Spring Session principal index: invalidate one operator's sessions safely",
        summary="Finding every session for a principal requires an indexed session repository; deleting by an unverified session ID risks another user's login.",
        blocks=[
            ("Choose the indexed repository deliberately", "The basic Redis session repository can look up a session by ID but does not provide principal search. An indexed repository supports findByPrincipalName and adds index maintenance. Use it when a parcel-console administrator must revoke all sessions after a credential reset. [[spring/session-redis-replicas|Shared session storage]] alone does not create that search capability."),
            ("Check ownership before deletion", "For a self-service device logout, first list sessions for the authenticated principal, then delete only an ID found in that set. A global administrator action needs a separate authorization check and audit record. Expiration and index events also need operational testing, especially with clustered Redis, because stale index entries can remain even when a session has expired. [[spring/method-authorization|Method authorization]] should guard the action, not the UI button alone."),
            ("Prove revocation", "Log the same operator into two browsers, revoke one session, and confirm the other still works. Then revoke all sessions after a credential reset and confirm both fail on the next request. This sketch is only a repository selection; it does not implement the administrative endpoint or its audit trail."),
        ],
        code='spring:\n  session:\n    redis:\n      repository-type: indexed\n      namespace: parcel-console:session', language="yaml",
        cost="Principal indexes add Redis writes and keys. Plan cleanup, expiration checks and bounded administrative lookups for accounts with many sessions.",
        mistakes=["Do not call findByPrincipalName on a repository configured without indexing.", "Do not delete a user-supplied session ID before checking it belongs to the intended principal.", "Do not assume an expired index entry proves an active session exists."],
        related=["spring/session-redis-replicas", "spring/session-fixation-login", "spring/method-authorization", "spring/oauth2-login-session"],
    ),
    dict(
        slug="rabbit-prefetch-memory", section="spring/production", subject="spring-production",
        title="Spring AMQP prefetch: bound unacknowledged messages before raising concurrency",
        summary="Rabbit listener prefetch controls how many messages a consumer can hold without acknowledgment, not how many it has committed.",
        blocks=[
            ("Count in-flight bytes", "A parcel-photo event can carry 420 KiB of metadata and thumbnails. With prefetch 250, one consumer may hold roughly 103 MiB of payload before object overhead; four concurrent consumers can multiply that pressure. Lower prefetch when messages are large, handlers are slow or strict ordering matters. [[spring/bounded-executor-rejection|An executor limit]] does not remove messages already delivered to listener containers."),
            ("Tie acknowledgement to the effect", "A listener may commit a database change and lose its connection before the broker records the acknowledgment. The event can be redelivered, even with a low prefetch. Keep [[spring/consumer-dedup-transaction|the dedup key and business write]] in one database transaction. Prefetch is capacity control, not exactly-once processing."),
            ("Measure under a stalled handler", "Run two consumers, block one handler, publish 47 messages, and measure unacknowledged count, heap use and distribution. Lower prefetch until memory and fairness meet the service budget. The property sketch assumes a simple listener container; a direct container or per-listener factory needs its own configuration check."),
        ],
        code='spring:\n  rabbitmq:\n    listener:\n      simple:\n        prefetch: 23\n        concurrency: 2\n        max-concurrency: 4', language="yaml",
        cost="Smaller prefetch limits memory and can improve fairness, but adds broker round trips and may lower throughput. Measure with production-sized messages.",
        mistakes=["Do not equate prefetch with completed transactions.", "Do not raise concurrency without accounting for prefetch times message size.", "Do not assume prefetch one prevents redelivery after a lost acknowledgment."],
        related=["spring/rabbit-reject-dead-letter", "spring/consumer-dedup-transaction", "spring/kafka-listener-manual-ack", "spring/bounded-executor-rejection"],
    ),
    dict(
        slug="rabbit-reject-dead-letter", section="spring/production", subject="spring-production",
        title="Spring AMQP poison messages: reject, requeue and dead-letter are different decisions",
        summary="A listener failure can requeue forever unless the container and broker have an explicit retry and dead-letter policy.",
        blocks=[
            ("Classify the failure", "A temporary ledger database outage may merit a bounded retry. A malformed parcel event with a missing tenant ID will not become valid after a thousand deliveries. By default, a failed listener can be requeued, so the same message may form a hot loop. AmqpRejectAndDontRequeueException marks an individual failure as non-requeueable; a broker dead-letter exchange must exist if the team wants to retain that rejected message. [[spring/kafka-retry-and-poison|Kafka poison handling]] has a different binder and offset model."),
            ("Keep the dead-letter path observable", "Record message ID, schema revision, rejection reason and tenant without dumping credentials or payload secrets. A dead-letter queue needs capacity, retention and a human replay procedure. After a parser fix, replay through the normal consumer with [[spring/consumer-dedup-transaction|the business dedup key]] intact. Blindly returning every dead-lettered message to the main queue can recreate the original loop."),
            ("Test the broker topology", "Send one invalid event and one valid event. Assert the invalid event reaches the dead-letter queue once, the valid one commits, and the listener remains available. Then test a transient failure with the configured retry limit. This code marks one rejection; without a bound queue and dead-letter exchange, the broker may discard it."),
        ],
        code='@RabbitListener(queues = "parcel-events")\npublic void applyParcel(ParcelEvent event) {\n    if (event.tenantId() == null) {\n        throw new AmqpRejectAndDontRequeueException("missing tenant identity");\n    }\n    parcelLedger.applyOnce(event);\n}',
        cost="Dead-letter storage and bounded retries add broker traffic. Requeue loops consume CPU and can starve valid messages, so track redelivery count and queue age.",
        mistakes=["Do not assume rejecting without requeue automatically creates a dead-letter queue.", "Do not retry permanent validation failures indefinitely.", "Do not replay dead-letter records without a dedup and repair plan."],
        related=["spring/rabbit-prefetch-memory", "spring/rabbit-publisher-confirm-return", "spring/consumer-dedup-transaction", "spring/relay-dead-letter"],
    ),
    dict(
        slug="rabbit-publisher-confirm-return", section="spring/production", subject="spring-production",
        title="RabbitTemplate confirms and returns: broker acceptance is not consumer completion",
        summary="Publisher confirms report broker acceptance; mandatory returns report unroutable messages, and neither proves the consumer committed its database work.",
        blocks=[
            ("Observe two failure channels", "A parcel relay can publish to an exchange that exists but has no matching queue. The broker may confirm accepting that publish while returning the message as unroutable when mandatory returns are enabled. A missing exchange can close the channel instead. Check the correlated confirm and the returned-message result before marking an outbox row delivered. [[spring/outbox-claim-lease|The outbox lease]] still needs an atomic acknowledgment of the relay's final decision."),
            ("Do not infer downstream success", "A positive broker confirm says nothing about whether a listener parsed the event or committed a ledger row. Keep distinct states for stored, broker-accepted and business-applied. The consumer's [[spring/consumer-dedup-transaction|dedup transaction]] handles retries if the publisher cannot know whether the broker saw an attempt. Use a stable event ID in CorrelationData so callbacks can resolve the right outbox row."),
            ("Break routing in a test", "Publish one message through a bound routing key and one through an unbound key. Assert the first receives a confirm without return, and the second is observed as returned. Then stop the broker during publish and verify the outbox row remains eligible for retry. These properties enable observation only; callback wiring and persistence still need implementation."),
        ],
        code='spring:\n  rabbitmq:\n    publisher-confirm-type: correlated\n    publisher-returns: true\n    template:\n      mandatory: true', language="yaml",
        cost="Confirms and returns add callback state and broker round trips. Keep a bounded number of outstanding correlations and expire them when the connection fails.",
        mistakes=["Do not mark an outbox row delivered merely because convertAndSend returned.", "Do not treat a broker confirm as a consumer commit.", "Do not enable returns while leaving mandatory publication disabled for the path that needs routing checks."],
        related=["spring/rabbit-reject-dead-letter", "spring/outbox-claim-lease", "spring/outbox-fenced-ack", "spring/kafka-producer-completion"],
    ),
    dict(
        slug="graphql-batch-mapping-n-plus-one", section="spring/web-apis", subject="spring-web",
        title="Spring GraphQL @BatchMapping: collapse N+1 lookups without changing field behavior",
        summary="A GraphQL field resolver called once per parent can turn one page request into N database queries; @BatchMapping groups those parent keys for one fetch.",
        blocks=[
            ("Count database calls", "A query returns 47 parcel records and asks for each parcel's depot. A naïve @SchemaMapping loads one depot for every parcel, making 48 database calls instead of a bounded batch. @BatchMapping receives the parents as a list and can fetch their depot IDs in one query, returning a map from each original parent to its depot. [[spring/graphql-bounded-list|Page bounds]] still matter: batching 47 rows is manageable, batching 47,000 can exhaust memory or exceed a database parameter limit."),
            ("Preserve missing-value semantics", "The batch map may omit a parent whose depot was removed. Decide whether the schema field is nullable and whether omission becomes null or a field error. [[spring/graphql-schema-nullability|Non-null fields]] can cause error propagation into the parent response. Use stable equality for parent keys if they are map keys; a mutable entity whose hash changes while loading can lose its result."),
            ("Verify the query shape", "Request 47 parcels with depots, assert the result IDs match their parents, and measure query count. Repeat with a missing depot and a page boundary. The method below is a mapping sketch; the repository method must include tenant scope and a bounded IN query before it is safe for production."),
        ],
        code='@BatchMapping(typeName = "Parcel", field = "depot")\nMap<Parcel, Depot> depot(List<Parcel> parcels, Principal principal) {\n    UUID tenantId = tenantResolver.requireTenant(principal);\n    Set<Long> depotIds = parcels.stream()\n        .map(Parcel::depotId).collect(Collectors.toSet());\n    Map<Long, Depot> depots = depotRepository\n        .findByTenantIdAndIdIn(tenantId, depotIds).stream()\n        .collect(Collectors.toMap(Depot::id, Function.identity()));\n    return parcels.stream().filter(parcel -> depots.containsKey(parcel.depotId()))\n        .collect(Collectors.toMap(Function.identity(),\n            parcel -> depots.get(parcel.depotId())));\n}',
        cost="One batched lookup lowers round trips but can create a large IN query and a map proportional to page size. Bound the parent list and measure SQL plan changes.",
        mistakes=["Do not claim N+1 is fixed if the repository still loops per ID.", "Do not use mutable parent keys without stable equals and hashCode.", "Do not ignore how a missing related row interacts with schema nullability."],
        related=["spring/graphql-batch-tenant-scope", "spring/graphql-bounded-list", "spring/graphql-schema-nullability", "spring/jpa-fetch-plans"],
    ),
    dict(
        slug="graphql-batch-tenant-scope", section="spring/security", subject="spring-security",
        title="Spring GraphQL batch loader tenant scope: never key a shared cache by row ID alone",
        summary="Batch loading reduces queries, but a loader that drops tenant identity or uses a cross-request cache can return another tenant's row.",
        blocks=[
            ("Carry authorization into the batch", "A GraphQL request contains parcel IDs 47 and 52. The batch fetch must still apply the authenticated tenant predicate; selecting by ID alone is a data leak even if the top-level parcel list was filtered. Spring's BatchLoaderRegistry creates DataLoaders per request and gives access to GraphQL context. That per-request cache is useful, but a separate application-wide cache keyed only by depot ID can cross tenant boundaries. [[spring/graphql-tenant-read|Top-level authorization]] does not automatically secure nested data fetchers."),
            ("Choose the cache key", "If depot IDs are tenant-local, include tenant ID in every cache and repository key. If IDs are globally unique, still enforce authorization at read time; uniqueness is not permission. A batch that merges parents from different GraphQL fields can carry distinct field arguments, so a simple @BatchMapping is insufficient when the nested field's filter changes by parent. Use the registry's context-aware loader in that case."),
            ("Test a collision", "Create tenant A and tenant B with the same local depot number, query each as a separate principal, and verify the nested result stays within its tenant. Reverse request order to catch stale cache reuse. The repository call below shows the predicate; the surrounding loader and security context need an integration test."),
        ],
        code='Map<Long, Depot> loadDepots(UUID tenantId, Set<Long> depotIds) {\n    return depotRepository.findByTenantIdAndIdIn(tenantId, depotIds)\n        .stream().collect(Collectors.toMap(Depot::id, Function.identity()));\n}',
        cost="Tenant predicates add an index requirement on tenant ID plus row ID. Per-request caches cap data lifetime but still grow with query breadth; apply field and page limits.",
        mistakes=["Do not infer nested-field authorization from the root resolver's check.", "Do not reuse a DataLoader cache across requests without tenant-aware keys.", "Do not batch across differing field arguments as if every parent had the same filter."],
        related=["spring/graphql-batch-mapping-n-plus-one", "spring/graphql-tenant-read", "spring/tenant-jdbc-predicate", "spring/tenant-receipt-authorization"],
    ),
    dict(
        slug="boot-trace-client-builder", section="spring/production", subject="spring-production",
        title="Spring Boot tracing across RestClient: construct the client from Boot's builder",
        summary="A new RestClient built outside the auto-configured builder can make an outgoing request appear as a new trace instead of a child span.",
        blocks=[
            ("Keep the trace chain", "The parcel API calls the rate service after accepting a request. Spring Boot instruments clients created from its auto-configured RestClient.Builder; creating a separate RestClient from scratch can omit propagation interceptors. The downstream service then logs a different trace ID, making one operation look like two. [[spring/restclient-request-factory|Request-factory selection]] and [[spring/restclient-timeout-budget|timeouts]] still apply to the same client; tracing is not a replacement for a deadline."),
            ("Avoid trusting client-supplied trace claims", "Trace headers help correlate work; they are not authentication or authorization data. A malicious caller can supply a trace ID, so keep tenant and identity checks in [[spring/jwt-resource-server|the security boundary]]. Do not place tokens or parcel addresses in span attributes. Instrument a stable operation name and bounded low-cardinality tags."),
            ("Follow one request", "Call the parcel API, let it call the rate service, and compare trace IDs and parent-child spans in the collector. Repeat with the client created outside the managed builder to demonstrate the gap. This bean is only a client-construction sketch; tracing dependencies, exporter and sampling still need configuration."),
        ],
        code='@Bean\nRestClient rateClient(RestClient.Builder builder) {\n    return builder.baseUrl("https://rate-service.internal")\n        .build();\n}',
        cost="Tracing adds context propagation and exporter traffic. A low sample rate reduces storage but can hide individual failures; use logs and metrics for unsampled requests.",
        mistakes=["Do not construct a new unmanaged RestClient and assume Boot propagation follows it.", "Do not treat trace headers as an identity source.", "Do not put secrets or high-cardinality personal data into span tags."],
        related=["spring/boot-observation-context-handoff", "spring/async-trace-context", "spring/restclient-request-factory", "spring/metric-cardinality"],
    ),
    dict(
        slug="boot-observation-context-handoff", section="spring/production", subject="spring-production",
        title="Spring Boot observation context across @Async and Reactor handoffs",
        summary="Observation context does not follow an arbitrary thread or reactive operator unless the corresponding propagation path is configured.",
        blocks=[
            ("Find the thread switch", "An HTTP request starts a trace, then submits parcel scoring to @Async. A new thread does not inherit ThreadLocal observation state by default. For Boot's auto-configured AsyncTaskExecutor, opt into context propagation. For a custom executor, use a ContextPropagatingTaskDecorator. Reactor operators have their own context path; automatic ThreadLocal restoration is controlled separately. [[spring/transaction-thread-boundary|Database transactions]] also do not cross the handoff merely because the trace does."),
            ("Limit what travels", "Context propagation is for observation state, not a substitute for passing an explicit tenant ID or business correlation key. When a detached task outlives the HTTP request, record its durable job ID and start a meaningful new span if necessary. [[spring/async-vs-durable-delivery|An in-process task]] can disappear during restart even if its trace looked complete."),
            ("Test two paths", "Capture a request trace ID, invoke the async scorer, and assert its span stays attached with propagation enabled. Run the same check through a Reactor chain when that stack is used. Force an executor rejection too: no child span should be mistaken for completed business work. The configuration below targets Boot-managed executors; a custom pool needs its own decorator."),
        ],
        code='spring:\n  task:\n    execution:\n      propagate-context: true\n  reactor:\n    context-propagation: auto', language="yaml",
        cost="Capturing and restoring context adds allocation and bookkeeping at each handoff. Measure high-volume task paths and keep baggage small.",
        mistakes=["Do not assume ThreadLocal trace state appears in a new worker thread.", "Do not use propagated observation context as the tenant authorization source.", "Do not confuse a recorded async span with durable task completion."],
        related=["spring/boot-trace-client-builder", "spring/async-trace-context", "spring/transaction-thread-boundary", "spring/async-vs-durable-delivery"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
for index, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    assert all(target in titles for target in item["related"]), path
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    body += ('<h2>Implementation sketch</h2><pre><code class="language-' + item.get("language", "java") + '">' + html.escape(item["code"], quote=False) + "</code></pre>")
    body += "<h2>Cost and verification</h2><p>" + prose(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + prose(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2><p>" + ", ".join('<a href="/' + target + '">' + html.escape(titles[target]) + "</a>" for target in item["related"]) + ".</p>"
    row = copy.deepcopy(by_path["spring/component-scan-vs-bean"])
    row.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path, title=item["title"], summary=item["summary"], body=body,
        subject=item["subject"], tags=["spring", item["subject"], item["slug"]],
        sort_order=4800 + index, published_at=stamp, created_at=stamp, updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7; current Spring Session, AMQP or GraphQL where relevant",
        "java_version": "21 or later",
        "verification_suite": "Editorial API contract review; implementation sketch not compiled",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

for section, heading in [
    ("spring/security", "Shared sessions and nested query authorization"),
    ("spring/production", "Rabbit delivery and trace handoffs"),
    ("spring/web-apis", "GraphQL relation batching"),
]:
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({"title": heading, "summary": "Follow state and ownership across process boundaries.", "lessons": paths})
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp
parent = by_path["spring/spring-boot"]
parent["body"] += "<h2>Sessions, messages and query execution</h2><ul>" + "".join(
    '<li><a href="/spring/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>" for item in lessons
) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("spring/oauth2-login-session", "spring/session-redis-replicas"),
    ("spring/session-csrf-boundary", "spring/session-cookie-policy"),
    ("spring/kafka-listener-manual-ack", "spring/rabbit-prefetch-memory"),
    ("spring/relay-dead-letter", "spring/rabbit-reject-dead-letter"),
    ("spring/graphql-bounded-list", "spring/graphql-batch-mapping-n-plus-one"),
    ("spring/graphql-tenant-read", "spring/graphql-batch-tenant-scope"),
    ("spring/async-trace-context", "spring/boot-observation-context-handoff"),
    ("spring/restclient-request-factory", "spring/boot-trace-client-builder"),
]:
    row = by_path[source]
    row["body"] += '<h2>Related boundary</h2><p><a href="/' + target + '">' + html.escape(titles[target]) + "</a></p>"
    row["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring articles")

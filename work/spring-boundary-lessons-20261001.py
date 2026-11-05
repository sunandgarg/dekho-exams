"""Add original Spring failure-boundary lessons and connect them to the curriculum."""

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
        slug="jpa-bulk-update-managed-state", section="spring/data-transactions",
        title="Spring Data JPA bulk update: the managed entity can still hold the old value",
        summary="A JPQL update changes database rows without rewriting objects already held in the persistence context.",
        blocks=[
            ("Keep the database and context apart", "A reservation service loads a WarehouseBalance, then issues a repository update that marks the same SKU unavailable. The SQL changes a row, but the loaded entity can still report available=true. A later flush of that managed object may write stale state. An update count says how many database rows matched; it says nothing about synchronized Java objects. This is the boundary behind [[spring/jpa-entity-lifecycle|entity state]] and [[spring/jpa-optimistic-locking|version checks]]."),
            ("Choose a deliberate cleanup", "The repository method below flushes pending changes before the update and clears managed objects after it. That prevents the old balance instance from masquerading as fresh state, but every managed object becomes detached. The service must reload anything it needs afterward. Use a small transaction; do not clear a context holding unrelated, unflushed work. If the command needs entity callbacks or versioned writes, mutate the managed entity instead of using bulk JPQL."),
            ("Make the test inspect both views", "Start a transaction, load one balance, run the bulk update, and assert the affected-row count and a fresh database read. Repeat with a managed object already present. The second assertion catches the stale-context failure that a repository-only test misses. This page is an implementation sketch; its exact mapping and SQL dialect need an application integration test."),
        ],
        code="@Modifying(flushAutomatically = true, clearAutomatically = true)\n@Query(\"update WarehouseBalance b set b.available = false \" +\n       \"where b.tenantId = :tenantId and b.sku = :sku\")\nint disableSku(String tenantId, String sku);",
        cost="The bulk statement is one database update for the matching set, but clearing the context forces later reads to hydrate entities again. A per-entity path can cost more round trips while preserving lifecycle behavior.",
        mistakes=["Do not assume @Modifying refreshes previously loaded entities by default.", "Do not enable clearAutomatically while relying on unrelated unflushed entities.", "Do not use a bulk update when entity callbacks or optimistic version increments are part of the contract."],
        related=["spring/jpa-entity-lifecycle", "spring/jpa-optimistic-locking", "spring/jpa-derived-delete-lifecycle", "spring/transactions"],
    ),
    dict(
        slug="jpa-derived-delete-lifecycle", section="spring/data-transactions",
        title="Spring Data JPA derived delete versus bulk delete: callbacks and memory cost",
        summary="A derived delete loads matching entities for removal; a JPQL delete issues a bulk statement and skips entity removal callbacks.",
        blocks=[
            ("The names hide different work", "Deleting expired ParcelHold rows by a derived delete method first selects the matching entities and removes them one by one. That path can run @PreRemove and JPA cascades. A JPQL delete sends one statement to the database; already managed ParcelHold objects stay stale and entity callbacks are bypassed. The SQL count can match while the application behavior differs."),
            ("Put side effects outside lifecycle assumptions", "If removal must publish a durable event, write an outbox row in the same transaction through an explicit service, then delete under a policy whose behavior you test. An entity callback alone is a poor substitute for [[spring/transaction-events|transaction-aware effects]] or [[spring/relay-transaction-boundaries|an outbox]]. Bulk delete is a reasonable fit for maintenance data when the business contract does not depend on callbacks or entity-level cascades."),
            ("Bound the operation", "A derived delete of 64 rows may be ordinary; one that loads millions of rows can exhaust heap before flush. Partition by a stable key and measure query count, memory and lock duration. A bulk delete still needs an indexed predicate and an explicit transaction. This example is an interface sketch, not a measured throughput result."),
        ],
        code="long deleteByTenantIdAndExpiredTrue(String tenantId);\n\n@Modifying(clearAutomatically = true)\n@Query(\"delete from ParcelHold h where h.tenantId = :tenantId \" +\n       \"and h.expired = true\")\nint deleteExpiredInBulk(String tenantId);",
        cost="Derived deletion uses O(n) entity memory for n matches and may issue multiple deletes; bulk JPQL can use one statement but bypasses per-entity work. Database scan and lock costs still depend on the predicate and indexes.",
        mistakes=["Do not expect @PreRemove to fire for a JPQL bulk delete.", "Do not infer low memory use from a derived method returning only a count.", "Do not switch deletion style without checking cascades, audit and outbox contracts."],
        related=["spring/jpa-bulk-update-managed-state", "spring/jpa-entity-lifecycle", "spring/relay-transaction-boundaries", "spring/jpa-fetch-plans"],
    ),
    dict(
        slug="jpa-pessimistic-lock-transaction", section="spring/data-transactions",
        title="Spring Data JPA pessimistic lock: hold it only through the stock decision",
        summary="A PESSIMISTIC_WRITE query is useful only when the read and mutation share the transaction that holds the database lock.",
        blocks=[
            ("Make the lock cover the decision", "A stock allocator reads one DepotSlot, checks that 47 units remain, then subtracts 12. Without a concurrency control rule, two requests may both see 47. A repository query with PESSIMISTIC_WRITE can serialize that decision for the row, provided the service method is transactional and the database honors the lock mode. Returning the entity and deciding later, after commit, loses the protection."),
            ("Keep external work out", "Do not call a payment service or broker while holding the row lock. Decide, persist, and commit; then use [[spring/relay-transaction-boundaries|a transactional outbox]] for delivery. A lock wait can consume a pooled connection and request thread. Compare this path with [[spring/jpa-optimistic-locking|optimistic locking]] when contention is rare."),
            ("Test the real database", "Launch two transactions against the same slot and prove the accepted quantity never exceeds the starting balance. Include a timeout path and an independent tenant ID. The behavior of lock hints, isolation and timeout differs by database; an H2-only check is insufficient for a deployment claim. The code is an implementation sketch."),
        ],
        code="@Lock(LockModeType.PESSIMISTIC_WRITE)\n@Query(\"select s from DepotSlot s where s.tenantId = :tenantId \" +\n       \"and s.sku = :sku\")\nOptional<DepotSlot> lockSlot(String tenantId, String sku);\n\n@Transactional\npublic void allocate(String tenantId, String sku, int units) {\n    DepotSlot slot = slots.lockSlot(tenantId, sku).orElseThrow();\n    slot.reserve(units);\n}",
        cost="A row lock trades conflict retries for waiting and possible deadlocks. It can lower throughput on a hot SKU, so bound the transaction and record lock-wait latency.",
        mistakes=["Do not assume the lock survives after the repository transaction returns.", "Do not hold the lock across remote calls.", "Do not treat an in-memory database concurrency test as proof for the deployed database."],
        related=["spring/jpa-optimistic-locking", "spring/transaction-isolation-choice", "spring/relay-transaction-boundaries", "spring/jpa-bulk-update-managed-state"],
    ),
    dict(
        slug="requires-new-connection-budget", section="spring/data-transactions",
        title="Spring REQUIRES_NEW: budget the second database connection",
        summary="An inner REQUIRES_NEW scope can need another physical connection while the outer transaction still owns one.",
        blocks=[
            ("Count simultaneous borrowers", "Suppose 24 request workers each start an outer transaction and then enter an audit method marked REQUIRES_NEW. The outer work can keep 24 connections occupied while the inner scopes wait for 24 more. With a pool of 24, no worker can acquire its inner connection. Even a pool of 25 merely permits one inner scope to make progress at a time. This is a capacity problem, not a rollback annotation problem."),
            ("Separate transaction intent from durability", "The inner audit can commit even if the outer reservation rolls back. That may be right for a failed-attempt record, but wrong for an event claiming a reservation succeeded. For success events, [[spring/relay-transaction-boundaries|the outbox path]] keeps the record and state change in one physical transaction. [[spring/transaction-propagation|Propagation choices]] should follow the failure contract."),
            ("Exercise a saturation case", "Drive concurrent calls up to the request pool limit, measure connection acquisition waits, and verify the business result after a timeout. Include other pool consumers such as health checks and scheduled work. The arithmetic here is a planning scenario; actual pool size depends on measured concurrent transaction scopes and database capacity."),
        ],
        code="@Transactional\npublic void reserve(ReservationCommand command) {\n    inventory.reserve(command);\n    attemptRecorder.record(command.requestId()); // separate bean\n}\n\n@Transactional(propagation = Propagation.REQUIRES_NEW)\npublic void record(String requestId) {\n    attempts.insert(requestId);\n}",
        cost="A REQUIRES_NEW call may consume a second pooled connection per active outer transaction. Extra connections increase database sessions and contention; undersizing turns the inner call into a pool wait or timeout.",
        mistakes=["Do not assume REQUIRES_NEW reuses the suspended outer connection.", "Do not call the inner method through self-invocation and expect proxy advice.", "Do not commit a success event independently of a business transaction that can still fail."],
        related=["spring/transaction-propagation", "spring/proxy-self-invocation", "spring/relay-transaction-boundaries", "spring/transaction-thread-boundary"],
    ),
    dict(
        slug="transaction-thread-boundary", section="spring/data-transactions",
        title="Spring imperative transaction: a worker thread does not inherit it",
        summary="PlatformTransactionManager binds its transaction to the current thread; Executor tasks need their own explicit boundary.",
        blocks=[
            ("The caller's annotation ends at the thread", "A controller invokes a transactional IntakeService, then submits a Runnable to an Executor. The task can start before the caller commits, and it does not inherit the caller's transaction. If the task queries the intake row, it may see no row or an old row depending on isolation. If it writes, that write may commit even after the caller rolls back. Copying a SecurityContext or trace ID does not transfer a database transaction."),
            ("Move work across a durable boundary", "For required follow-up work, insert a job or outbox record in the caller's transaction and let a separate worker claim it after commit. For disposable parallel computation, pass immutable input and collect results before committing the caller's decision. When the task itself writes to a database, give that worker its own service transaction. [[spring/async-vs-durable-delivery|Async delivery]] and [[spring/transaction-events|transaction events]] cover different failure windows."),
            ("Verify ordering and rollback", "A useful test blocks the worker, rolls the caller back, then releases the worker. The worker must not write a success marker for a reservation that never committed. The sketch names the boundary; it does not establish queue durability or retry semantics."),
        ],
        code="@Transactional\npublic void accept(IntakeCommand command) {\n    intakes.insert(command.id(), command.units());\n    pendingJobs.insert(command.id(), \"RECOUNT\");\n}\n\n@Transactional\npublic void processPending(String intakeId) {\n    Intake intake = intakes.get(intakeId);\n    counts.recount(intake);\n}",
        cost="A durable job row adds one write and later polling or notification. Passing an imperative transaction into an Executor is not a supported way to save that cost.",
        mistakes=["Do not expect @Transactional to follow CompletableFuture or @Async onto another thread.", "Do not treat afterCommit publication as durable delivery by itself.", "Do not let a worker act on state that the caller may still roll back."],
        related=["spring/async-boundaries", "spring/async-vs-durable-delivery", "spring/relay-transaction-boundaries", "spring/requires-new-connection-budget"],
    ),
    dict(
        slug="reactive-transaction-context-ownership", section="spring/data-transactions",
        title="Spring reactive transaction: subscription owns the context, not a thread",
        summary="ReactiveTransactionManager carries transaction state in Reactor context, so work outside the subscribed chain is outside that transaction.",
        blocks=[
            ("Build one chain", "A reactive debit should insert its ledger row and update the account in one publisher chain, then apply a TransactionalOperator to that chain. The operator does not cover a second publisher subscribed manually inside doOnNext. That detached subscription can run after the first has failed or been cancelled. [[spring/r2dbc-subscription-boundary|Subscription timing]] is part of the transaction contract."),
            ("Handle cancellation as a business case", "A client disconnect can cancel a response publisher. If the transaction's completion depends on that publisher, cancellation can change when the database work is rolled back. Do not tie an essential payment or stock commitment to a response stream without deciding what cancellation means. A durable command record can separate acceptance from the client's connection; [[spring/r2dbc-reactive-transaction|the debit lesson]] covers the normal rollback path."),
            ("Check the boundary under one subscription", "Use a real R2DBC connection factory and subscribe once to the returned publisher. Inject failure after the first write; verify both writes are absent. Then cancel before completion and check database state. This is an architecture sketch; cancellation behavior must be verified against the chosen driver and transaction manager."),
        ],
        code="Mono<Void> transfer = balances.debit(accountId, 47)\n    .then(ledger.record(accountId, 47))\n    .then();\nreturn transactionOperator.transactional(transfer);",
        cost="One reactive transaction occupies a database connection until terminal completion. Slow upstream work and never-ending publishers can keep that connection unavailable to the pool.",
        mistakes=["Do not call subscribe inside a transactional chain for a required write.", "Do not use a thread-local transaction assumption in Reactor code.", "Do not ignore cancellation when a client disconnects before completion."],
        related=["spring/r2dbc-reactive-transaction", "spring/r2dbc-subscription-boundary", "spring/r2dbc-test-isolation", "spring/transaction-thread-boundary"],
    ),
    dict(
        slug="jwt-issuer-audience-boundary", section="spring/security",
        title="Spring resource server JWT: validate both issuer and intended audience",
        summary="A valid signature and trusted issuer do not prove a token was issued for this API.",
        blocks=[
            ("Treat audience as a separate check", "An identity provider may sign tokens for a warehouse API and a billing API with the same key. The signature and issuer can both validate while the token was meant for billing. Configure the resource server's audience to the warehouse API's identifier. Scope checks still matter, but scope is not a substitute for aud: the recipient and the granted operation are different claims. [[spring/jwt-resource-server|Resource server setup]] establishes the filter path."),
            ("Make key distribution explicit", "A JWK Set URI supplies public verification keys; the resource server must still validate the issuer and audience. Pin accepted signature algorithms and allow a planned key overlap during rotation. Do not fetch a key URL from a token header. The verifier's trusted configuration owns that address. [[spring/jwt-tenant-principal|Tenant authorization]] remains a second check after token validation."),
            ("Test rejection, not only admission", "Use tokens with the right signature but wrong aud, right aud but wrong iss, expired time, and an unexpected algorithm. Assert 401 for invalid authentication before controller code runs. A successful call with one good token leaves most of the boundary untested."),
        ],
        code="spring:\n  security:\n    oauth2:\n      resourceserver:\n        jwt:\n          issuer-uri: ${WAREHOUSE_ISSUER_URI}\n          audiences: warehouse-ledger-api",
        language="yaml",
        cost="JWT verification is local after keys are available, but key retrieval, cache expiry and rotation still need an availability policy. Audience validation adds a small claim check, not a network round trip.",
        mistakes=["Do not accept a token solely because its signature matches a trusted key.", "Do not confuse an OAuth scope with the API audience.", "Do not trust a JWK Set URL supplied by the token itself."],
        related=["spring/jwt-resource-server", "spring/jwt-tenant-principal", "spring/security-authentication-vs-denial", "spring/jwt-web-context-test"],
    ),
    dict(
        slug="security-authentication-vs-denial", section="spring/security",
        title="Spring Security 401 versus 403: authentication and access are separate failures",
        summary="An unauthenticated request should enter authentication; an authenticated principal without permission should be denied access.",
        blocks=[
            ("Classify the rejected request", "A missing or invalid bearer token means the API cannot establish identity. The authentication entry point sends a 401 challenge. A valid token for an operator lacking the stock-adjust scope reaches authorization and should receive 403. ExceptionTranslationFilter routes these cases differently; a controller catch-all that maps both to 403 hides the real contract. [[spring/security-filter-chain|Filter order]] matters before controller code runs."),
            ("Avoid leaking details", "The response can identify the needed authentication scheme and a stable error code without echoing secrets or claims. Logs should record a request ID and the decision category, with care around token material. A browser login chain may redirect instead of returning JSON, so write route-specific tests for the actual chain selected by [[spring/security-matcher-order|request matchers]]."),
            ("Exercise the matrix", "Check no token, malformed token, valid token without authority, and valid token with authority. Assert status, challenge header where applicable, and that the protected service was not called on rejection. This page describes an HTTP contract; the exact handler configuration needs an application test."),
        ],
        code="mockMvc.perform(post(\"/api/stock/adjust\"))\n    .andExpect(status().isUnauthorized());\nmockMvc.perform(post(\"/api/stock/adjust\")\n        .with(jwt().authorities(new SimpleGrantedAuthority(\"SCOPE_stock.read\"))))\n    .andExpect(status().isForbidden());",
        cost="The distinction adds no material runtime cost. It improves client recovery: obtain credentials after 401; request permission or change operation after 403.",
        mistakes=["Do not return 403 for every missing-token request.", "Do not turn authorization failure into a login redirect for a bearer-token API.", "Do not expose token contents in an error body or application log."],
        related=["spring/security-filter-chain", "spring/security-matcher-order", "spring/jwt-issuer-audience-boundary", "spring/jwt-web-context-test"],
    ),
    dict(
        slug="session-fixation-login", section="spring/security",
        title="Spring Security login session: rotate the identifier at authentication",
        summary="An authenticated browser session must not keep an identifier that could have been fixed before login.",
        blocks=[
            ("Watch the transition", "A browser can have a session before login for a saved request or CSRF token. On successful authentication, Spring Security's session fixation protection changes the session ID on modern Servlet containers. The old identifier must not remain a usable authenticated session. This is distinct from [[spring/session-csrf-boundary|CSRF protection]]: one stops a known pre-login session ID from becoming an authenticated handle; the other protects state-changing browser requests."),
            ("Keep the default unless the application proves otherwise", "Custom authentication filters and manual SecurityContext persistence can alter when the authenticated context is saved. Test the entire login path, including the response cookie, old-cookie rejection and logout. A reverse proxy must preserve secure cookie behavior and HTTPS detection; [[spring/trusted-forwarded-headers|forwarded-header trust]] is part of that deployment."),
            ("Use a realistic browser test", "Capture the session cookie before login, authenticate, and compare it with the post-login cookie. Retry a protected route using only the old cookie and require rejection. Repeat after logout. This lesson is a test plan and sketch; no running browser flow is claimed."),
        ],
        code="MockHttpSession beforeLogin = new MockHttpSession();\nString oldId = beforeLogin.getId();\nMvcResult authenticated = mockMvc.perform(post(\"/login\")\n    .session(beforeLogin)\n    .with(csrf())\n    .param(\"username\", \"shift-lead\")\n    .param(\"password\", password))\n    .andReturn();\nassertNotEquals(oldId, authenticated.getRequest().getSession().getId());",
        cost="Changing a session identifier is cheap. Shared session storage, concurrent session control and invalidation behavior need their own load and failover checks.",
        mistakes=["Do not disable session fixation protection to keep a pre-login cookie stable.", "Do not assume JWT stateless APIs use the browser-session policy.", "Do not claim safety from an ID-change assertion without checking the old ID cannot authorize."],
        related=["spring/oauth2-login-session", "spring/session-csrf-boundary", "spring/trusted-forwarded-headers", "spring/security-filter-chain"],
    ),
    dict(
        slug="trusted-forwarded-headers", section="spring/web-apis",
        title="Spring behind a proxy: trust forwarded headers only after the edge strips them",
        summary="Forwarded and X-Forwarded headers can change the request scheme, host and client address seen by the application.",
        blocks=[
            ("Put trust at the network edge", "A service behind a TLS-terminating proxy may see plain HTTP internally while the browser used HTTPS. ForwardedHeaderFilter can reconstruct the external scheme and host for redirects and links. The application cannot tell whether a forwarded header came from its proxy or an arbitrary client. The outermost trusted proxy must remove incoming Forwarded and X-Forwarded variants, then set the values it intends the service to use."),
            ("Treat host and prefix as input", "If a client can inject X-Forwarded-Host, a password-reset link or absolute redirect may point to an attacker host. If the proxy cannot guarantee stripping, remove headers without using them. Keep an allowlist for externally valid hosts where link generation matters. [[spring/security-filter-chain|Security rules]] and [[spring/oauth2-login-session|OAuth callbacks]] must see a consistent external URL."),
            ("Test through the actual proxy", "Send a spoofed forwarded host from outside and verify the edge replaces it. Then request a legitimate HTTPS redirect and confirm its scheme and host. A local MockMvc test of the filter cannot prove the proxy's stripping behavior; the edge-to-service path is the system under test."),
        ],
        code="@Bean\nForwardedHeaderFilter forwardedHeaders() {\n    ForwardedHeaderFilter filter = new ForwardedHeaderFilter();\n    // Enable only behind a proxy that discards client-supplied variants.\n    return filter;\n}",
        cost="The filter's wrapping cost is small; the security cost of trusting unfiltered host or scheme values is large. Test redirect and cookie behavior after every proxy configuration change.",
        mistakes=["Do not trust raw Forwarded or X-Forwarded headers from public clients.", "Do not strip only one header family while accepting the other.", "Do not assume a filter unit test proves the reverse proxy is configured safely."],
        related=["spring/oauth2-login-session", "spring/session-fixation-login", "spring/cors-boundaries", "spring/security-filter-chain"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {
    "spring/data-transactions": "spring-data",
    "spring/security": "spring-security",
    "spring/web-apis": "spring-web",
}

for index, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    assert all(target in titles for target in item["related"]), path
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    language = item.get("language", "java")
    body += ('<h2>Implementation sketch</h2><pre><code class="language-' + language + '">'
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
        path=path,
        title=item["title"],
        summary=item["summary"],
        body=body,
        subject=subjects[item["section"]],
        tags=["spring", "spring-boot", item["section"].split("/")[-1], item["slug"]],
        sort_order=4500 + index,
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot",
        "section_path": item["section"],
        "kind": "tutorial",
        "content_format": "html",
        "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7 / Spring Security 7 where relevant",
        "java_version": "21 or later",
        "verification_suite": "Editorial API contract review; implementation sketch not compiled",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

for section in subjects:
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    if not paths:
        continue
    hub = by_path[section]
    heading = {
        "spring/data-transactions": "Persistence and transaction failure boundaries",
        "spring/security": "Token and browser-session boundaries",
        "spring/web-apis": "Proxy trust boundary",
    }[section]
    hub["data"]["modules"].append({
        "title": heading,
        "summary": "Trace the failure path, test the rejected case and follow the connected lesson.",
        "lessons": paths,
    })
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

# Put discovery links on the parent and relevant existing lessons, without
# changing their tested technical assertions.
parent = by_path["spring/spring-boot"]
parent["body"] += (
    '<h2>Production failure boundaries</h2><ul>'
    + "".join(
        '<li><a href="/spring/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
        for item in lessons
    ) + "</ul>"
)
parent["updated_at"] = stamp
for source, target in [
    ("spring/jpa-entity-lifecycle", "spring/jpa-bulk-update-managed-state"),
    ("spring/transaction-propagation", "spring/requires-new-connection-budget"),
    ("spring/r2dbc-reactive-transaction", "spring/reactive-transaction-context-ownership"),
    ("spring/jwt-resource-server", "spring/jwt-issuer-audience-boundary"),
    ("spring/oauth2-login-session", "spring/session-fixation-login"),
    ("spring/cors-boundaries", "spring/trusted-forwarded-headers"),
]:
    row = by_path[source]
    row["body"] += (
        '<h2>Related boundary</h2><p><a href="/' + target + '">'
        + html.escape(titles[target]) + "</a></p>"
    )
    row["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring articles; new total", sum(
    row["path"].startswith("spring/") and row["type"] == "article" for row in rows
))

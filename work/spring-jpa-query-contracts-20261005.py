"""Add eight original Spring Data JPA lessons to the local editorial fixture."""

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
        slug="jpa-entitygraph-toone-query",
        title="Spring Data JPA entity graph for a bounded to-one read",
        summary="Load a required to-one association with the receipt query instead of discovering an N+1 after mapping begins.",
        blocks=[
            ("Make the read shape explicit", "A receipt detail endpoint returns 47 rows and shows each account name. If mapping touches receipt.account and the association was left lazy, the ORM can issue one root query plus a separate account query for each uncached association. A repository method with an entity graph requests the account in the same read plan. The method remains tenant-scoped. This is a narrow application of [[spring/jpa-fetch-plans|fetch-plan design]], not a reason to mark every association eager."),
            ("Keep pagination away from collection fetches", "A to-one graph has at most one account per receipt, so it does not multiply receipt rows. A collection graph is different: joining receipt lines can multiply rows, interfere with page boundaries, or force expensive deduplication. For a list endpoint that needs a collection, page receipt IDs first and fetch details for those bounded IDs in a second query. [[spring/jpa-page-vs-slice|Page and Slice]] still need a stable order."),
            ("Verify the actual SQL", "Run the endpoint against 47 receipts that reference different accounts. Capture statement count and compare it with the query without a graph. Assert the response still contains only the authenticated tenant's receipts. An entity graph chooses fetch shape; it does not add an authorization predicate or guarantee one SQL statement under every provider and mapping."),
        ],
        code='interface ReceiptReadRepository extends JpaRepository<ReceiptEntity, UUID> {\n    @EntityGraph(attributePaths = "account")\n    List<ReceiptEntity> findTop47ByTenantIdOrderByCreatedAtDescIdDesc(\n        UUID tenantId);\n}',
        cost="A to-one join transfers account columns with each receipt row. That is often cheaper than dozens of round trips, but wider rows can be wasteful when the response does not need account data. Compare SQL and payload size on a representative read.",
        mistakes=["Do not use a collection entity graph on a paged query without checking row multiplication and page correctness.", "Do not assume a graph filters another tenant's rows; keep the tenant predicate.", "Do not replace SQL inspection with a repository mock."],
        related=["spring/jpa-fetch-plans", "spring/jpa-page-vs-slice", "spring/jpa-open-in-view-off", "spring/tenant-jdbc-predicate", "spring/spring-data-projections"],
    ),
    dict(
        slug="jpa-specification-tenant-scope",
        title="Spring Data JPA Specifications with a mandatory tenant predicate",
        summary="Compose optional search filters around a tenant condition that callers cannot remove.",
        blocks=[
            ("Separate optional filters from mandatory scope", "A back-office receipt search accepts an optional status and a date range. The tenant condition is not optional. Build it inside the service from the authenticated identity, then combine user-selected filters with it. A Specification describes a predicate; it does not decide whether a principal may read the tenant. Resolve that decision first through [[spring/tenant-claim-required|tenant identity checks]]."),
            ("Make the query bounded", "Passing an unbounded Pageable does not protect the database. Cap the requested page size, sort by createdAt and id, and decide whether the UI needs a total count. [[spring/jpa-page-vs-slice|A Slice]] can omit the count when the UI only needs a next-page flag. An index beginning with tenantId and supporting the chosen filter and order can matter more than the Java predicate syntax."),
            ("Test composition, not just each piece", "Seed receipts for two tenants with the same status and timestamp. Search with status supplied and absent; both results must stay inside the authenticated tenant. Then test an empty date interval and a malicious tenant ID supplied in request data. The service must ignore that caller-supplied scope. Inspect the generated SQL for repeated joins before adding more Specifications."),
        ],
        code='static Specification<ReceiptEntity> visibleReceipts(\n        UUID authenticatedTenantId, ReceiptStatus requestedStatus) {\n    Specification<ReceiptEntity> tenant = (root, query, builder) ->\n        builder.equal(root.get("tenantId"), authenticatedTenantId);\n    if (requestedStatus == null) return tenant;\n    return tenant.and((root, query, builder) ->\n        builder.equal(root.get("status"), requestedStatus));\n}',
        cost="Predicate composition itself is small. Database work depends on selectivity, indexes, joins, and whether a count query is requested. An optional filter that prevents an index range scan can dominate the endpoint's cost.",
        mistakes=["Do not accept the tenant ID from a request field as an authorization decision.", "Do not return an unbounded search because the Specification reads cleanly.", "Do not assume individually tested predicates prove the combined query is tenant-safe."],
        related=["spring/tenant-claim-required", "spring/jpa-page-vs-slice", "spring/pagination-bounds", "spring/tenant-jdbc-predicate", "spring/jpa-count-query-joins"],
    ),
    dict(
        slug="jpa-page-vs-slice",
        title="Spring Data JPA Page versus Slice: pay for totals only when needed",
        summary="A Slice reports whether another window exists without the total-count work a Page may require.",
        blocks=[
            ("Match the return type to the screen", "An activity feed needs 47 receipts and a next button. It does not display an exact page count. Returning Page asks the repository infrastructure for total metadata and can issue a count query; returning Slice fetches enough rows to determine whether another slice exists. That saves count work, but it does not make the data query free. Use [[spring/jpa-count-query-joins|a deliberate count query]] when an admin report truly needs an exact total."),
            ("Use a deterministic order", "Ordering only by createdAt is unstable when two receipts share a timestamp. Add id as a tie-breaker, and keep both columns in the query's order. With offset pagination, a new row inserted between requests can still shift later results. For deep scrolling or strong continuation semantics, use [[spring/keyset-pagination|a keyset cursor]] with an index matching the filter and order."),
            ("Prove the query budget", "Request the first and second slices from a dataset larger than one page; assert hasNext is accurate and IDs do not repeat in the unchanged dataset. Record the SQL. Then request a large offset to observe the database work, and cap page size with [[spring/pagination-bounds|input bounds]]. A Slice is a count-cost choice, not a cure for deep offset scans."),
        ],
        code='interface ReceiptFeedRepository extends JpaRepository<ReceiptEntity, UUID> {\n    Slice<ReceiptEntity> findByTenantId(\n        UUID tenantId, Pageable page);\n}\n\nPageable firstWindow = PageRequest.of(0, 47,\n    Sort.by(Sort.Order.desc("createdAt"),\n            Sort.Order.desc("id")));',
        cost="A Slice typically reads one extra row to determine hasNext. A Page can require a separate count query, especially expensive with joins. Both offset forms may scan or skip increasing work as the requested page number grows.",
        mistakes=["Do not request Page totals for a screen that never displays them.", "Do not sort on a non-unique timestamp alone.", "Do not describe Slice as keyset pagination; it still uses an offset with Pageable."],
        related=["spring/jpa-count-query-joins", "spring/keyset-pagination", "spring/pagination-bounds", "spring/jpa-specification-tenant-scope", "spring/jpa-entitygraph-toone-query"],
    ),
    dict(
        slug="jpa-count-query-joins",
        title="Spring Data JPA count query for a joined Page",
        summary="Count distinct parent rows when a filter joins a to-many relationship, and verify the page metadata against real SQL.",
        blocks=[
            ("A joined row is not always one receipt", "A receipt with three matching lines can appear three times in a SQL join. If the content query selects distinct receipts but the count query counts joined rows, the UI may claim more receipts than exist. Define the count expression explicitly for a Page query that filters on receipt lines. The example counts distinct receipt IDs and keeps the tenant predicate in both queries."),
            ("Know when the count is worth it", "Count distinct may require extra sorting or hashing in the database, depending on the plan and index. If the screen only needs a next button, [[spring/jpa-page-vs-slice|a Slice]] may avoid the total count; still test the joined content query for duplicates and stable boundaries. For a large report where exact totals matter, benchmark the count separately and consider a dedicated read model rather than hiding the expense in a repository method."),
            ("Compare content and total", "Seed one receipt with multiple matching lines, one with a single matching line, and a matching receipt in another tenant. The first page must contain two distinct local receipts and report totalElements as two. Run the test against the actual database dialect used in deployment. A unit mock cannot expose a wrong JPQL count or provider-specific pagination behavior."),
        ],
        code='@Query(\n    value = "select distinct receipt from ReceiptEntity receipt " +\n        "join receipt.lines line where receipt.tenantId = :tenantId " +\n        "and line.sku = :sku",\n    countQuery = "select count(distinct receipt.id) from ReceiptEntity receipt " +\n        "join receipt.lines line where receipt.tenantId = :tenantId " +\n        "and line.sku = :sku")\nPage<ReceiptEntity> findByTenantAndLineSku(\n    UUID tenantId, String sku, Pageable page);',
        cost="The content query and count query are separate database work. DISTINCT can add memory and sort/hash work; an index on line sku and join keys plus a tenant-selective access path may help, but inspect the actual execution plan.",
        mistakes=["Do not count joined rows when the page displays distinct parent entities.", "Do not forget the tenant predicate in the count query.", "Do not trust in-memory repository doubles to validate JPQL, SQL plans, or page totals."],
        related=["spring/jpa-page-vs-slice", "spring/jpa-specification-tenant-scope", "spring/jpa-fetch-plans", "spring/spring-data-projections", "spring/keyset-pagination"],
    ),
    dict(
        slug="jpa-saveandflush-not-commit",
        title="Spring Data JPA saveAndFlush is a SQL boundary, not a commit",
        summary="Flush can surface a database constraint error before method return while the surrounding transaction may still roll back.",
        blocks=[
            ("Distinguish three events", "save places or merges entity state in the persistence context. Flush synchronizes pending changes with the database inside the current transaction. Commit makes the transaction durable and visible according to database isolation. Calling saveAndFlush can force a unique-key rejection earlier, but a later failure still rolls back the flushed row. [[spring/transactions|Transaction ownership]] remains at the service boundary, not the repository call."),
            ("Do not publish on flush", "An order acceptance service writes a receipt and an outbox row in one transaction. If it sends a broker message immediately after saveAndFlush, a later rollback can leave a message announcing a receipt that never committed. Persist an outbox obligation in the same database transaction and deliver it later through [[spring/relay-transaction-boundaries|the relay boundary]]. A flush also does not make a concurrent transaction see an uncommitted row."),
            ("Exercise the rollback path", "Save a receipt with a unique tenant and external key, flush it, then throw a test exception before method exit. Assert the row is absent in a new transaction. Repeat with a duplicate key to check when the exception appears for the chosen database and constraint mode. Some constraints are deferred until commit, so do not promise that every violation is caught by flush."),
        ],
        code='@Transactional\npublic UUID accept(ReceiptCommand command) {\n    ReceiptEntity receipt = receipts.saveAndFlush(\n        ReceiptEntity.from(command));\n    outbox.save(OutboxEvent.receiptAccepted(receipt.getId()));\n    return receipt.getId();\n}',
        cost="An explicit flush adds a synchronization point and can reduce batching opportunities. Use it when an earlier database check or generated value is required, not after every save. The transaction still holds resources until commit or rollback.",
        mistakes=["Do not treat saveAndFlush as a durable commit.", "Do not send an external message after flush and before commit.", "Do not assume every database constraint is checked before commit."],
        related=["spring/transactions", "spring/relay-transaction-boundaries", "spring/jpa-bulk-update-managed-state", "spring/jpa-readonly-transaction-hint", "spring/jpa-optimistic-locking"],
    ),
    dict(
        slug="jpa-readonly-transaction-hint",
        title="Spring read-only transaction: performance hint, not a write guard",
        summary="Use readOnly for a read unit of work, but enforce write permissions and invariants elsewhere.",
        blocks=[
            ("Name the promise accurately", "A receipt view service loads a tenant-scoped row and maps it to an immutable response within a read-only transaction. Spring passes the read-only flag to transaction infrastructure; with Hibernate, the chosen flush behavior can skip dirty-check work for a large loaded graph. The flag is not an authorization rule and should not be used as the only defense against a mutation. [[spring/transaction-proxies|Proxy invocation]] still controls whether the annotation is applied."),
            ("Keep reads bounded and contained", "Return a DTO while the transaction is active rather than exposing a lazy entity to the controller. Pair the read with [[spring/jpa-open-in-view-off|disabled Open EntityManager in View]] so a later response serializer cannot silently query the database. A projection may avoid loading an entire entity graph. Inherited Spring Data CRUD reads are commonly configured read-only, while declared query methods and outer service transactions deserve explicit review."),
            ("Test what matters", "Assert that a denied principal cannot call the write path; do not use a readOnly test as proof of denial. Measure statement count and allocation for a representative read, then inspect the transaction attributes at the service proxy. A database driver or provider may treat read-only differently, so benchmark instead of promising a fixed speedup."),
        ],
        code='@Transactional(readOnly = true)\npublic ReceiptView readReceipt(UUID tenantId, UUID receiptId) {\n    ReceiptEntity receipt = receipts.findByTenantIdAndId(\n        tenantId, receiptId).orElseThrow(ReceiptNotFound::new);\n    return new ReceiptView(receipt.getId(), receipt.getTotalMinor());\n}',
        cost="A read-only hint can reduce flush and dirty-check overhead with some providers. The dominant cost may still be SQL, hydrated columns, and N+1 reads. A read transaction holds a connection until it exits.",
        mistakes=["Do not interpret readOnly as a security boundary or universal database write prohibition.", "Do not return a lazy entity to be serialized after the transaction closes.", "Do not assume a self-invoked annotated method entered a transaction proxy."],
        related=["spring/transaction-proxies", "spring/jpa-open-in-view-off", "spring/spring-data-projections", "spring/jpa-entitygraph-toone-query", "spring/tenant-claim-required"],
    ),
    dict(
        slug="jpa-auditing-actor-context",
        title="Spring Data JPA auditing: record the actor at the write boundary",
        summary="Populate created-by and modified-by fields from authenticated context without treating audit metadata as access control.",
        blocks=[
            ("Capture actor identity deliberately", "A receipt write records who created or last changed it. Enable JPA auditing, attach the auditing listener to the entity, and provide AuditorAware from the current authentication. Store a stable subject identifier, not a display name that changes next month. The audit field answers who the application recorded; it does not prove a caller was authorized. [[spring/method-security-proxy-boundary|Method security]] and tenant predicates remain separate."),
            ("Define non-request writers", "Scheduled jobs, queue consumers and migration programs may have no HTTP security context. Choose an explicit service actor for each path or reject the write; do not silently invent a human identity. An imperative SecurityContextHolder is thread-local, so [[spring/transaction-thread-boundary|worker threads]] need their own authenticated execution context and transaction. Keep the actor in the same transaction as the row so a rollback removes both changes."),
            ("Verify the lifecycle", "Create and update a receipt through Spring-managed repository methods and assert the two actor fields in a fresh persistence context. Test an unauthenticated write path and a worker job. Bulk JPQL updates bypass ordinary entity listeners, so use a separate audit design for those operations; [[spring/jpa-bulk-update-managed-state|bulk-update behavior]] is its own contract."),
        ],
        code='@Configuration\n@EnableJpaAuditing\nclass ReceiptAuditConfiguration {\n    @Bean AuditorAware<String> currentActor() {\n        return () -> Optional.ofNullable(\n            SecurityContextHolder.getContext().getAuthentication())\n            .filter(actor -> actor.isAuthenticated()\n                && !(actor instanceof AnonymousAuthenticationToken))\n            .map(Authentication::getName);\n    }\n}\n\n@Entity\n@EntityListeners(AuditingEntityListener.class)\nclass ReceiptEntity {\n    @Id UUID id;\n    @CreatedBy @Column(nullable = false) String createdBy;\n    @LastModifiedBy String modifiedBy;\n}',
        cost="Auditing callbacks write extra columns and inspect caller context on entity changes. The overhead is usually small beside SQL, but bulk imports and high-volume updates need a measured design because entity callbacks may not run.",
        mistakes=["Do not treat an audit field as proof of authorization.", "Do not let a background writer silently record an absent or misleading human actor.", "Do not expect JPQL bulk updates to invoke entity auditing callbacks."],
        related=["spring/jpa-bulk-update-managed-state", "spring/method-security-proxy-boundary", "spring/transaction-thread-boundary", "spring/jpa-saveandflush-not-commit", "spring/tenant-claim-required"],
    ),
    dict(
        slug="jpa-open-in-view-off",
        title="Spring Boot Open EntityManager in View: close the response-time query gap",
        summary="Disable request-wide persistence access and fetch or project the data needed before the service returns.",
        blocks=[
            ("A serializer can become a query caller", "A controller returns a JPA entity. After the service transaction ends, JSON serialization touches a lazy association. With Open EntityManager in View enabled, that traversal can issue SQL during response rendering, outside the deliberate service read plan. With it disabled, the missing fetch becomes visible as a lazy-loading failure. Prefer a DTO whose fields were assembled inside a bounded service transaction. [[spring/jpa-entitygraph-toone-query|A to-one graph]] or [[spring/spring-data-projections|a projection]] can supply the required fields."),
            ("Choose one read boundary", "Set spring.jpa.open-in-view=false in application configuration, then identify endpoints that returned entities. Move mapping into the service and make the required associations explicit. Do not respond by turning every relationship eager; that expands unrelated queries and can multiply rows on collections. A read-only service method states intent, while [[spring/jpa-readonly-transaction-hint|the hint]] alone does not pick the correct fetch plan."),
            ("Test serialization end to end", "Run a real HTTP test with SQL statement counting. Assert that serialization performs no unexpected database queries and that the response stays correct after the service transaction closes. An endpoint that needs 47 records should not accidentally make 47 association round trips. Watch connection hold time and response latency before and after the change; disabling Open EntityManager in View exposes assumptions that must be repaired endpoint by endpoint."),
        ],
        code='spring.jpa.open-in-view=false',
        code_language="properties",
        cost="Closing the request-wide persistence context avoids late SQL and may shorten connection use. Deliberate DTO mapping can add code and additional targeted queries; count those queries instead of assuming the configuration alone improves latency.",
        mistakes=["Do not return a JPA entity as an HTTP response and rely on serialization to choose its fetch plan.", "Do not fix a lazy-loading failure by making every association eager.", "Do not assume switching the property repairs existing endpoints without response-level tests."],
        related=["spring/jpa-entitygraph-toone-query", "spring/spring-data-projections", "spring/jpa-readonly-transaction-hint", "spring/jpa-fetch-plans", "spring/jpa-page-vs-slice"],
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
    language = item.get("code_language", "java")
    body += ('<h2>Implementation contract</h2><pre><code class="language-' + language + '">'
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
        subject="spring-data", tags=["spring", "spring-data-jpa", item["slug"]],
        sort_order=5500 + number, published_at=stamp, created_at=stamp,
        updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": "spring/data-transactions",
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7 / Spring Data JPA 4 where relevant",
        "java_version": "21 or later",
        "verification_suite": "Spring Data JPA API contract review; repository snippets require an application entity model",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

paths = ["spring/" + item["slug"] for item in lessons]
hub = by_path["spring/data-transactions"]
hub["data"]["modules"].append({
    "title": "JPA query and transaction contracts",
    "summary": "Bounded reads, count costs, flush timing, actor auditing, and response-time SQL.",
    "lessons": paths,
})
for route in ("spring/data-transactions", "spring/spring-boot"):
    entry = by_path[route]
    entry["body"] += "<h2>JPA query and transaction contracts</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    entry["updated_at"] = stamp

for source, target in [
    ("spring/jpa-fetch-plans", "spring/jpa-entitygraph-toone-query"),
    ("spring/tenant-claim-required", "spring/jpa-specification-tenant-scope"),
    ("spring/keyset-pagination", "spring/jpa-page-vs-slice"),
    ("spring/spring-data-projections", "spring/jpa-count-query-joins"),
    ("spring/transactions", "spring/jpa-saveandflush-not-commit"),
    ("spring/transaction-proxies", "spring/jpa-readonly-transaction-hint"),
    ("spring/jpa-bulk-update-managed-state", "spring/jpa-auditing-actor-context"),
    ("spring/jpa-entity-lifecycle", "spring/jpa-open-in-view-off"),
]:
    entry = by_path[source]
    entry["body"] += ('<h2>Related JPA contract</h2><p><a href="/' + target + '">'
                      + html.escape(titles[target]) + "</a></p>")
    entry["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring Data JPA lessons")

"""Add original Spring Data MongoDB, Elasticsearch and method-security lessons."""

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
        slug="mongodb-versioned-document", section="spring/data-transactions",
        title="Spring Data MongoDB optimistic locking: save the version you read",
        summary="A MongoDB @Version field turns a stale document save into a detectable conflict when writes are acknowledged.",
        blocks=[
            ("A read-copy-write is a race", "Two stock clerks load the same ParcelAllocation document at version 6. Both change its reservedUnits. Without a version condition, the later save can overwrite the earlier decision. With @Version, Spring Data adds the observed version to the write predicate and increments it on a successful update; a stale save raises OptimisticLockingFailureException. That is a conflict signal, not an automatic merge. [[spring/jpa-optimistic-locking|JPA version checks]] solve a similar application problem through a different store."),
            ("Decide the retry contract", "For a commutative increment, an atomic MongoDB update can avoid loading and replacing the full document. For a decision that depends on several fields, reload the latest document and re-evaluate the invariant after a conflict. Do not simply replay a stale object until it saves. Include tenantId in the query path so a valid document ID cannot select another tenant's allocation; [[spring/tenant-claim-required|identity validation]] happens before persistence."),
            ("Prove the conflict", "Load two copies, save one, then attempt to save the other. Assert the second write fails and the first value remains. Use acknowledged writes; unacknowledged write concern can hide the failure. The entity sketch does not define a complete repository or HTTP conflict response, so test those boundaries separately."),
        ],
        code='@Document("parcel_allocations")\nclass ParcelAllocation {\n    @Id String id;\n    String tenantId;\n    int reservedUnits;\n    @Version Long version;\n}',
        cost="A versioned save adds a version predicate and conflict path. Under high contention, retries increase read and write traffic; a single atomic update may be cheaper for a simple counter.",
        mistakes=["Do not interpret an optimistic conflict as a request to overwrite with the stale document.", "Do not use unacknowledged writes when the caller needs conflict detection.", "Do not treat a document ID alone as tenant authorization."],
        related=["spring/jpa-optimistic-locking", "spring/mongodb-tenant-unique-index", "spring/mongodb-transaction-session", "spring/tenant-claim-required"],
    ),
    dict(
        slug="mongodb-tenant-unique-index", section="spring/data-transactions",
        title="Spring Data MongoDB tenant uniqueness: enforce it in an index",
        summary="A read-before-insert check cannot guarantee uniqueness under concurrent requests; a compound unique index can.",
        blocks=[
            ("The race is between the two reads", "Two requests for tenant-west both check that invoiceCode INV-47 is unused. Both reads return empty. If the application relies on that check, both inserts can succeed. A unique index over tenantId and invoiceCode makes the database reject the second insert. A global unique index on invoiceCode would reject a legitimate invoice with the same code in another tenant."),
            ("Treat index creation as a deployment step", "Spring Data MongoDB does not enable automatic index creation by default. An @CompoundIndex annotation documents the mapping, but an existing production collection still needs a reviewed migration that checks duplicate data before creating the index. Build the index ahead of the application change, record the rollout, and test the duplicate-key exception path. [[spring/schema-expand-column|Expand-before-use]] is the same release principle in a relational store."),
            ("Assert both dimensions", "Insert INV-47 twice in tenant-west and require one rejection. Insert INV-47 in tenant-east and require success. Inspect the actual index specification in the database; a repository mock cannot prove uniqueness. Return a stable conflict response rather than leaking the raw database error. The annotation is a mapping sketch, not evidence the index exists in production."),
        ],
        code='@Document("invoice_reservations")\n@CompoundIndex(name = "tenant_invoice_unique",\n    def = "{\'tenantId\': 1, \'invoiceCode\': 1}", unique = true)\nclass InvoiceReservation {\n    @Id String id;\n    String tenantId;\n    String invoiceCode;\n}',
        cost="Each insert or update maintains the compound index. The extra write cost buys a database-enforced invariant across every application replica.",
        mistakes=["Do not rely on existsBy... followed by insert for a uniqueness guarantee.", "Do not assume the annotation created an index on an existing deployment.", "Do not omit tenantId from a tenant-scoped unique key."],
        related=["spring/mongodb-versioned-document", "spring/tenant-claim-required", "spring/schema-expand-column", "spring/testcontainers-migration-ownership"],
    ),
    dict(
        slug="mongodb-transaction-session", section="spring/data-transactions",
        title="Spring Data MongoDB transaction: keep every write in one client session",
        summary="A MongoDB transaction depends on a client session and an explicit transaction manager; an annotation alone is not enough.",
        blocks=[
            ("Name the unit of work", "A transfer changes two wallet documents and writes one transfer record. A single-document update is atomic, but these three writes need a multi-document transaction if the product promises all-or-nothing state. Register MongoTransactionManager for imperative operations, use the same MongoDatabaseFactory in the template, and enter through a Spring-managed service proxy. MongoDB transactions require a suitable replica set or sharded deployment; a standalone local server is not a valid proof."),
            ("Keep I/O inside the session", "MongoTemplate participates in the bound session. A raw driver collection obtained separately may need the ClientSession passed explicitly; otherwise the write can escape the intended transaction. Do not send a broker message or remote HTTP call before commit and call that atomic. [[spring/relay-transaction-boundaries|An outbox]] records a later delivery obligation in the transaction. [[spring/transaction-thread-boundary|Worker threads]] do not inherit the imperative session."),
            ("Test rollback on the real topology", "Cause the third write to fail after the first two have executed. Assert neither wallet changed and no transfer record exists. Repeat with a direct-driver write to catch an accidental escape from the session. The code is the service boundary; repository methods and transaction manager wiring must be verified in an application integration test."),
        ],
        code='@Transactional\npublic void transfer(TransferCommand command) {\n    wallets.debit(command.sourceWallet(), command.units());\n    wallets.credit(command.targetWallet(), command.units());\n    transfers.insert(command.id(), command.units());\n}',
        cost="A multi-document transaction holds session resources and can increase contention. Prefer an atomic single-document update when the business invariant fits one document.",
        mistakes=["Do not assume @Transactional activates MongoDB transactions without a Mongo transaction manager.", "Do not mix a session-aware template with an unrelated raw driver write.", "Do not hold the transaction open across a broker or HTTP call."],
        related=["spring/mongodb-versioned-document", "spring/transaction-thread-boundary", "spring/relay-transaction-boundaries", "spring/reactive-transaction-context-ownership"],
    ),
    dict(
        slug="mongodb-bulk-write-callbacks", section="spring/data-transactions",
        title="Spring Data MongoDB bulk writes: fewer round trips, different lifecycle behavior",
        summary="Bulk operations reduce request overhead but do not carry every per-entity callback and version behavior of repository saves.",
        blocks=[
            ("A batch is not N ordinary saves", "A nightly allocation import writes thousands of independent documents. MongoTemplate bulk operations group writes into fewer requests, which can lower network overhead. That does not make a bulk update equivalent to calling save on each aggregate. Lifecycle event publication is limited for bulk work, and version behavior depends on the chosen operation. A service that relies on callbacks for audit or validation may silently lose that work when switched to bulk."),
            ("Choose failure ordering", "Ordered bulk execution stops at a failed operation; unordered execution can continue with other writes. Neither mode automatically gives a business-level all-or-nothing import. Record a source digest and per-row outcome, reject duplicate import IDs, and reconcile partial success. [[spring/batch-input-snapshot|Batch input identity]] and [[spring/batch-skip-quarantine|quarantine]] are useful when the import spans many chunks."),
            ("Measure the actual gain", "Compare request count and elapsed time on realistic document sizes. Inject one duplicate-key failure in the middle and inspect which records committed. Verify any versioned document behavior explicitly against [[spring/mongodb-versioned-document|the optimistic-locking contract]]. The snippet only names the operation mode; import validation and result reconciliation remain application code."),
        ],
        code='BulkOperations writes = mongoTemplate.bulkOps(\n    BulkOperations.BulkMode.ORDERED, ParcelAllocation.class);\nwrites.insert(validatedAllocations);\nBulkWriteResult result = writes.execute();\nassertEquals(validatedAllocations.size(), result.getInsertedCount());',
        cost="Bulk writes save round trips but can increase the size of a failed unit. Memory and server work scale with batch size; keep a bounded chunk and record partial outcomes.",
        mistakes=["Do not assume bulk operations trigger every repository lifecycle callback.", "Do not call an ordered bulk import an atomic transaction.", "Do not ignore partial success when one row is rejected."],
        related=["spring/mongodb-versioned-document", "spring/mongodb-tenant-unique-index", "spring/batch-input-snapshot", "spring/batch-skip-quarantine"],
    ),
    dict(
        slug="mongodb-change-stream-resume", section="spring/data-transactions",
        title="Spring Data MongoDB change stream: resume token and idempotent projection",
        summary="A change stream can resume after a disconnect when its token is retained; the consumer must still handle replay and token expiry.",
        blocks=[
            ("The token is a recovery cursor", "A product-search projector watches a MongoDB collection and updates a search index. After processing one event, it stores the event's resume token along with projector progress. On restart it resumes from that token rather than starting at the current time and silently skipping an outage window. Change streams require a replica set or sharded cluster. A timestamp is a weaker recovery cursor when events share a time boundary."),
            ("Make replay harmless", "Persisting the search update and the MongoDB resume token in different systems cannot be one ordinary database transaction. A crash between them can replay the event. Use document ID plus source version as an idempotency key, and let the target reject older versions. [[spring/stomp-reconnect-snapshot|Reconnect snapshots]] solve a related gap for browsers; [[spring/relay-dead-letter|dead-letter handling]] covers poison events after repeated failure."),
            ("Drill the outage", "Stop the projector, write several source versions, restart from the saved token, and verify the final target version. Then force an expired or invalid token and define a full-rebuild path instead of pretending the stream continued. The code names the resume API; token persistence, lease ownership and target writes are separate application responsibilities."),
        ],
        code='ChangeStreamOptions options = ChangeStreamOptions.builder()\n    .resumeAfter(savedResumeToken)\n    .build();\nFlux<ChangeStreamEvent<ParcelAllocation>> events =\n    reactiveMongoTemplate.changeStream(\n        "parcel_allocations", options, ParcelAllocation.class);',
        cost="A change stream holds a server cursor and a client connection. Projection retries and rebuilds consume target-index capacity; retain only the cursor state needed for recovery.",
        mistakes=["Do not acknowledge progress before the target projection is durable.", "Do not assume a change stream is available on a standalone MongoDB server.", "Do not treat an expired resume token as permission to skip missed data."],
        related=["spring/mongodb-versioned-document", "spring/relay-dead-letter", "spring/stomp-reconnect-snapshot", "spring/elasticsearch-index-alias-rollout"],
    ),
    dict(
        slug="elasticsearch-refresh-visibility", section="spring/data-transactions",
        title="Spring Data Elasticsearch write versus search: refresh is the visibility boundary",
        summary="An acknowledged index operation does not by itself mean an immediate search will see the document.",
        blocks=[
            ("Distinguish write acknowledgement from search visibility", "An order-search document is indexed and the HTTP write returns success. A search request made immediately afterward can still miss it until Elasticsearch refreshes the relevant shard. A direct get by ID and a search have different visibility paths. Do not write a test that asserts immediate search visibility without choosing a refresh policy. [[spring/mongodb-change-stream-resume|An asynchronous projector]] adds another delay before the write even reaches Elasticsearch."),
            ("Choose where to pay", "For an admin workflow that must search a newly written document, request a refresh behavior or refresh the index in a narrow test. Refreshing after every write lowers indexing throughput and can increase segment work. For a public feed, show the accepted write from the primary database while search catches up, or return a versioned pending state. The source database remains the system of record."),
            ("Test the two paths", "Index a document, immediately read it by ID, and search for it before and after an explicit index refresh. Assert the UI's promised behavior, not a timing accident on a fast local node. The snippet forces visibility only for a controlled test or narrow operation; it is not a blanket production setting."),
        ],
        code='IndexOperations index = elasticsearchOperations.indexOps(\n    IndexCoordinates.of("orders-read-v4"));\nindex.refresh();\nSearchHits<OrderSearchDocument> hits = elasticsearchOperations.search(\n    searchQuery, OrderSearchDocument.class);',
        cost="Refresh work increases as write rate rises. A delayed-search contract can preserve indexing throughput, but the UI must not claim the result is complete before the projection catches up.",
        mistakes=["Do not equate write acknowledgement with immediate search visibility.", "Do not refresh the index after every write without measuring the indexing cost.", "Do not use a search index as the only durable record of an order."],
        related=["spring/mongodb-change-stream-resume", "spring/elasticsearch-sequence-conflict", "spring/elasticsearch-index-alias-rollout", "spring/relay-transaction-boundaries"],
    ),
    dict(
        slug="elasticsearch-sequence-conflict", section="spring/data-transactions",
        title="Spring Data Elasticsearch sequence conflict: do not overwrite a newer projection",
        summary="Sequence number and primary term can reject a stale full-document reindex; source-version checks protect the business projection order.",
        blocks=[
            ("Two versions exist", "Elasticsearch assigns a sequence number and primary term to a stored document. Spring Data can carry those values on a loaded entity and use them when indexing it again, rejecting a stale write with an optimistic-locking failure. Separately, an event projector may receive business version 84 after version 91 because of replay. Elasticsearch's concurrency metadata protects against concurrent index operations, but a fresh write of old business data can still be wrong unless the projector compares the source version."),
            ("Set a source ordering rule", "Store sourceVersion inside the search document and reject any update whose source version is not newer than the indexed one. Keep the same document ID across retries. A projector that gives every replay a new random ID makes deduplication impossible. [[spring/mongodb-change-stream-resume|MongoDB resume tokens]] and [[spring/kafka-idempotent-consumer|idempotent consumers]] both need this target-side rule."),
            ("Test out-of-order delivery", "Apply source version 91, then deliver 84 and 91 again. The indexed version must remain 91 and no duplicate document may appear. Also load one Elasticsearch entity twice, index one copy, then assert the second stale copy conflicts. The entity field sketch exposes the index-level mechanism; the source-version rule requires explicit projector code."),
        ],
        code='@Document(indexName = "orders-read-v4")\nclass OrderSearchDocument {\n    @Id String orderId;\n    long sourceVersion;\n    SeqNoPrimaryTerm indexVersion;\n}',
        cost="Version checks add comparisons and conflict retries. They protect data quality; a full rebuild may still be cheaper than repairing many silently stale search documents.",
        mistakes=["Do not confuse Elasticsearch's sequence number with the domain source version.", "Do not assign a new document ID to every replay of one order.", "Do not retry a stale full-document write without reloading current state."],
        related=["spring/elasticsearch-refresh-visibility", "spring/mongodb-change-stream-resume", "spring/kafka-idempotent-consumer", "spring/elasticsearch-index-alias-rollout"],
    ),
    dict(
        slug="elasticsearch-index-alias-rollout", section="spring/data-transactions",
        title="Spring Data Elasticsearch mapping rollout: build a new index, then move the read alias",
        summary="A field mapping change is an index migration; a read alias permits validation before traffic switches.",
        blocks=[
            ("Do not mutate a live search contract blindly", "A catalog search field changes from analyzed text to an exact keyword. Existing index data and queries still use the old mapping. Create catalog-v5 with the new mapping, backfill documents from the source of record, and compare counts and representative queries before moving the catalog-read alias. The Spring entity can point at that alias while index creation is owned by a deployment step. This keeps index lifecycle out of ordinary application startup."),
            ("Account for writes during the backfill", "If writes continue while catalog-v5 builds, track source versions and replay changes until the new index catches up. Switch the alias only when the index reaches a recorded checkpoint. After the switch, keep catalog-v4 long enough for rollback and old clients, then retire it under a separate change. [[spring/elasticsearch-sequence-conflict|Source-version checks]] prevent an old event from reversing the backfill. [[spring/schema-contract-gate|Contract gates]] are the relational equivalent."),
            ("Verify the alias, not just the new index", "Query catalog-v5 directly, then query catalog-read before and after the alias switch. Exercise a rollback and confirm the application does not auto-create an empty index under the alias name. The annotation below declares an alias target; index creation, backfill and alias update are controlled operations, not performed by this Java class."),
        ],
        code='@Document(indexName = "catalog-read", createIndex = false)\nclass CatalogSearchDocument {\n    @Id String productId;\n    @Field(type = FieldType.Keyword) String sku;\n    @Field(type = FieldType.Text) String description;\n}',
        cost="Dual indices temporarily double index storage and backfill I/O. That cost buys a measured cutover and rollback path instead of an unreviewed mapping change on live traffic.",
        mistakes=["Do not let application startup silently create an empty replacement index.", "Do not switch the read alias before the backfill catches up with live writes.", "Do not delete the old index in the same operation that changes the alias."],
        related=["spring/elasticsearch-refresh-visibility", "spring/elasticsearch-sequence-conflict", "spring/mongodb-change-stream-resume", "spring/schema-contract-gate"],
    ),
    dict(
        slug="method-security-proxy-boundary", section="spring/security",
        title="Spring method security: authorization advice runs through the bean proxy",
        summary="@EnableMethodSecurity activates method interceptors, but an internal call on this does not pass through the proxy.",
        blocks=[
            ("The controller is not the only entry point", "A stock-adjust service may be called from a controller, scheduled job, message listener or another service. A request matcher cannot guard all four. @PreAuthorize on the service method can enforce a caller authority at that boundary after @EnableMethodSecurity is configured. The annotation does not secure every unannotated method automatically, so keep a catch-all web rule and review service entry points."),
            ("Avoid self-invocation", "If an unprotected method on the same object calls this.adjustStock(), that call bypasses proxy advice. Move the protected operation into a separate injected Spring bean, or enforce the decision explicitly through an AuthorizationManager. [[spring/proxy-self-invocation|The proxy boundary]] also affects transactions. Tenant claims must be compared with the method argument, not merely checked for presence; [[spring/tenant-claim-required|tenant validation]] remains a separate rule."),
            ("Test a non-web caller", "Call the service through a Spring-injected bean with a principal lacking the authority, and assert AccessDeniedException before the repository writes. Then invoke it through a message handler and verify the same rule. A MockMvc-only test may miss a self-invocation path that never enters the method interceptor."),
        ],
        code='@EnableMethodSecurity\n@Configuration\nclass MethodAuthorizationConfig {}\n\n@Service\nclass StockAdjustmentService {\n    @PreAuthorize("hasAuthority(\'SCOPE_stock.write\')")\n    public void adjust(String tenantId, StockChange change) {\n        stockLedger.apply(tenantId, change);\n    }\n}',
        cost="Method authorization adds an interceptor and expression evaluation per guarded call. A database authorization lookup inside every expression can dominate that cost and should be measured.",
        mistakes=["Do not assume @PreAuthorize runs on an internal this.method() call.", "Do not expect @EnableMethodSecurity to protect unannotated methods.", "Do not check only a broad scope when the method also accepts a tenant ID."],
        related=["spring/proxy-self-invocation", "spring/security-filter-chain", "spring/tenant-claim-required", "spring/method-security-postauthorize-side-effects"],
    ),
    dict(
        slug="method-security-postauthorize-side-effects", section="spring/security",
        title="Spring @PostAuthorize: denial happens after the method has run",
        summary="A post-invocation authorization check can prevent a return value from reaching the caller, but it cannot undo arbitrary side effects.",
        blocks=[
            ("Check timing before using returnObject", "A service loads a payroll record and @PostAuthorize checks that its owner matches the caller. The decision can inspect the returned object, but the method has already executed. If the method also sent a message, incremented a counter or called another service, denial does not rewind that work. For a write, prefer a pre-invocation rule based on authenticated tenant and arguments; use database predicates to enforce row ownership."),
            ("Keep the denied result contained", "Do not log the protected object before the post-check. A repository query should include tenant and owner filters where possible, limiting both data access and accidental exposure. [[spring/method-security-proxy-boundary|Method advice]] requires a proxy invocation. [[spring/security-authentication-vs-denial|A 403 response]] is the HTTP expression of an authenticated caller failing authorization, but message and batch callers need their own error mapping."),
            ("Probe the side effect", "Build a test method that would publish an event, then call it as a denied principal. If the event still appears, the policy is too late. Move the guard before the operation and repeat the test. The annotation sketch is appropriate only for a side-effect-free read with a return object whose owner is authoritative."),
        ],
        code='@PostAuthorize("returnObject.ownerId == authentication.name")\npublic PayrollView readPayroll(String payrollId) {\n    return payrollReadStore.load(payrollId);\n}',
        cost="A post-check may load a full record only to deny it, wasting I/O. A tenant-scoped query and pre-check usually cut this work while reducing the data-exposure surface.",
        mistakes=["Do not use @PostAuthorize to protect a method that performs an irreversible side effect.", "Do not log the returned object before post-authorization succeeds.", "Do not assume a denied return value means the database query never ran."],
        related=["spring/method-security-proxy-boundary", "spring/security-authentication-vs-denial", "spring/tenant-claim-required", "spring/relay-transaction-boundaries"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {"spring/data-transactions": "spring-data", "spring/security": "spring-security"}
for number, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    body += ('<h2>Implementation sketch</h2><pre><code class="language-java">'
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
        subject=subjects[item["section"]],
        tags=["spring", "spring-boot", item["section"].split("/")[-1], item["slug"]],
        sort_order=5100 + number, published_at=stamp, created_at=stamp, updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7 / Spring Data 2025-2026 where relevant",
        "java_version": "21 or later",
        "verification_suite": "Official API contract review; implementation sketch not compiled",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

for section, heading in {
    "spring/data-transactions": "MongoDB and Elasticsearch boundaries",
    "spring/security": "Method-level authorization",
}.items():
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({
        "title": heading,
        "summary": "Store-level invariants, search visibility and service authorization.",
        "lessons": paths,
    })
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["spring/spring-boot"]
parent["body"] += "<h2>Document data, search and method security</h2><ul>" + "".join(
    '<li><a href="/spring/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons
) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("spring/jpa-optimistic-locking", "spring/mongodb-versioned-document"),
    ("spring/tenant-claim-required", "spring/mongodb-tenant-unique-index"),
    ("spring/transaction-thread-boundary", "spring/mongodb-transaction-session"),
    ("spring/batch-input-snapshot", "spring/mongodb-bulk-write-callbacks"),
    ("spring/mongodb-change-stream-resume", "spring/elasticsearch-refresh-visibility"),
    ("spring/security-filter-chain", "spring/method-security-proxy-boundary"),
]:
    row = by_path[source]
    row["body"] += ('<h2>Related boundary</h2><p><a href="/' + target + '">'
                    + html.escape(titles[target]) + "</a></p>")
    row["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring articles; new total", sum(
    row["path"].startswith("spring/") and row["type"] == "article" for row in rows
))

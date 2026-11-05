"""Publish source-checked Spring GraphQL lessons with deliberate related paths."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
by = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def p(text):
    escaped = html.escape(text)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>", escaped) + "</p>"


lessons = [
    dict(slug="graphql-schema-nullability", section="spring/web-apis",
        title="Spring GraphQL schema nullability: trace one field failure through the response",
        summary="A GraphQL schema fixes field types and nullability before a resolver runs; a failed non-null field can null a larger part of the response.",
        blocks=[
            ("Treat the schema as an executable contract", [
                "The fixture declares receipt(id: ID!) as nullable because an ID can be absent or outside the tenant. It declares receipts(limit: Int!) as a non-null list of non-null Receipt values. A request without limit fails validation before the fetcher runs. A request selecting only id and available returns those fields; tenant is absent from the result, even though it exists on the server-side record. Field selection changes the response shape, not the authorization rule.",
                "The source kit builds the schema from an in-memory resource through GraphQlSource. A deployed Boot endpoint would load schema files and register controller or fetcher beans separately. This fixture does not expose an HTTP route. [[spring/graphql-service-tests|The test-layer lesson]] separates schema execution from transport registration."
            ]),
            ("Follow non-null propagation", [
                "The list fetcher rejects limit 47. Because receipts is declared non-null, its failure bubbles through the root query and the execution result has errors with null data. A nullable receipt lookup instead returns receipt: null for a missing or cross-tenant ID without nulling the entire query. Design nullability around actual failure semantics; making every field non-null can turn one unavailable child into a much larger null result. [[spring/graphql-error-boundary|Error handling]] is part of that choice."
            ]),
        ],
        code='''type Query {
  receipt(id: ID!): Receipt
  receipts(limit: Int!): [Receipt!]!
}
type Receipt {
  id: ID!
  tenant: String!
  available: Int!
  version: Int!
}''', language="graphql",
        proof="selectedFieldsAreReturnedForAuthorizedTenant, missingRequiredArgumentIsRejectedBeforeFetcher and oversizedListRequestReturnsGraphQlError",
        cost="GraphQL validates each operation against the schema before execution. The schema does not itself cap query depth, aliases or nested database work. This direct test has no HTTP endpoint or production query-cost policy.",
        mistakes=["Do not equate a selected field with permission to see its value.", "Do not mark a failure-prone field non-null without tracing propagation.", "Do not assume required arguments are equivalent to business validation."],
        related=["spring/graphql-error-boundary", "spring/graphql-bounded-list", "spring/graphql-tenant-read", "spring/graphql-service-tests", "spring/mvc-validation-problem"]),
    dict(slug="graphql-tenant-read", section="spring/security",
        title="Spring GraphQL tenant reads: scope every resolver before returning a record",
        summary="A GraphQL field resolver must check the caller's tenant against the requested record, regardless of which fields the client selects.",
        blocks=[
            ("Resolve identity outside the document", [
                "The test puts tenant north in the GraphQL execution context, then asks for RC-47. The resolver returns the matching record. The same ID under tenant south returns null, even when the document requests only id. An input argument or HTTP header supplied by the caller would not be a trusted tenant identity. In a deployed application, an authentication filter must establish the principal, and a GraphQL interceptor must attach its verified tenant to execution context. [[spring/tenant-receipt-authorization|The HTTP tenant boundary]] is a separate test of that trust path.",
                "Every root and nested fetcher that can expose tenant data needs its own ownership rule or a service method that enforces one centrally. A schema type being named Receipt carries no access control. Passing a whole JPA entity directly can expose fields later added to the schema through default property fetching; keep returned shapes narrow and test each field."
            ]),
            ("Avoid confusing absence with permission", [
                "Returning null for a cross-tenant receipt prevents the fixture from revealing the row. A real API must decide whether unknown and forbidden IDs are intentionally indistinguishable, then keep logging and audit detail private. The fixture has no login, token validation, membership registry or row-level database security. [[spring/graphql-service-tests|A transport-level test]] must prove the context came from verified credentials, not a test-supplied map."
            ]),
        ],
        code='''private Receipt receipt(DataFetchingEnvironment environment) {
    Receipt found = ledger.get(environment.getArgument("id"));
    return found != null && found.tenant().equals(tenant(environment))
        ? found : null;
}''', language="java",
        proof="selectedFieldsAreReturnedForAuthorizedTenant and tenantCannotReadAnotherTenantsReceipt",
        cost="A tenant predicate must be pushed into the database query in a real repository; loading a row and then checking it still incurs the read and can leak through timing or logging. This in-memory fixture proves only the returned field decision.",
        mistakes=["Do not trust a tenant value embedded in the GraphQL document.", "Do not authorize only the root query while nested fetchers bypass it.", "Do not treat this direct execution-context test as authentication coverage."],
        related=["spring/tenant-receipt-authorization", "spring/security-filter-chain", "spring/graphql-service-tests", "spring/graphql-optimistic-mutation", "spring/graphql-schema-nullability"]),
    dict(slug="graphql-bounded-list", section="spring/data-transactions",
        title="Spring GraphQL list bounds: reject large arguments before reading rows",
        summary="A list resolver needs an explicit maximum and a database-side limit; a GraphQL field selection alone does not bound row work.",
        blocks=[
            ("Validate the count at the resolver boundary", [
                "The fixture accepts limit 1 and returns the first north-tenant receipt after sorting by ID. It rejects 47 with a GraphQL error because its contract allows only 1 through 25. The test is intentionally small: the in-memory stream walks the ledger before limiting. A production query should enforce tenant, stable order and limit in SQL, plus a pagination cursor or offset contract. [[spring/keyset-pagination|Keyset pagination]] explains how to continue a stable ordered scan without an ever-growing offset.",
                "A client can ask for many aliased copies of the same field or nest expensive child selections under a bounded root list. A per-field limit is one control, not a complete operation cost budget. Decide maximum depth, total field work, timeouts and cancellation with measurements from real traffic. The source kit does not test those controls."
            ]),
            ("Keep ordering explicit", [
                "Without stable ordering, page boundaries can shift between requests and repeated rows can appear. The fixture sorts by receipt ID to make its one-page assertion deterministic. A real query should choose a unique tie-breaker and document what happens while rows are inserted or updated during pagination."
            ]),
        ],
        code='''private List<Receipt> receipts(DataFetchingEnvironment environment) {
    int limit = environment.getArgument("limit");
    if (limit < 1 || limit > 25) {
        throw new IllegalArgumentException("limit outside 1..25");
    }
    return ledger.values().stream()
        .filter(receipt -> receipt.tenant().equals(tenant(environment)))
        .sorted((left, right) -> left.id().compareTo(right.id()))
        .limit(limit).toList();
}''', language="java",
        proof="listIsTenantScopedAndBounded and oversizedListRequestReturnsGraphQlError",
        cost="The checked in-memory implementation sorts all matching records, so its cost is O(n log n) time and O(n) storage before limit. A database-side indexed tenant-and-ID query can avoid scanning and sorting the full set, but must be measured on the target engine.",
        mistakes=["Do not mistake the requested selection set for a query-cost cap.", "Do not apply a limit after loading every database row.", "Do not paginate without a stable order and tie-breaker."],
        related=["spring/keyset-pagination", "spring/graphql-schema-nullability", "spring/graphql-error-boundary", "spring/tenant-receipt-authorization", "spring/testing-boundaries"]),
    dict(slug="graphql-optimistic-mutation", section="spring/data-transactions",
        title="Spring GraphQL mutation versions: reject a stale stock reservation",
        summary="A mutation can require an expected version so a second writer cannot silently overwrite a changed receipt.",
        blocks=[
            ("Make the conflict a data rule", [
                "The checked mutation reserves seven units from RC-47 at version 3, leaving 12 units and version 4. A second request carrying expectedVersion 3 produces a GraphQL error and leaves the balance at 12. The in-memory ledger uses ConcurrentHashMap.computeIfPresent to make that one-process read-check-write atomic. A deployed database needs a conditional UPDATE with tenant, ID, version and stock floor in the predicate, followed by an affected-row check. [[spring/tenant-versioned-write|The JDBC lesson]] tests that database contract separately.",
                "A wrong-tenant mutation returns null and leaves RC-47 unchanged. The test injects tenant identity into GraphQL context itself; no authentication filter validates it. [[spring/graphql-tenant-read|Tenant resolver boundaries]] explain why that source of identity must change before deployment."
            ]),
            ("Keep side effects outside a failed write", [
                "If the mutation also emits an event, the event intent must be committed with the database change or published from a durable outbox. Sending to a broker before the versioned update succeeds can announce a reservation that never happened. [[spring/outbox-atomic-write|The outbox transaction]] and [[spring/kafka-outbox-handoff|broker handoff]] cover those cut points."
            ]),
        ],
        code='''Receipt result = ledger.computeIfPresent(id, (ignored, current) -> {
    if (!current.tenant().equals(tenant(environment))) return current;
    if (current.version() != expectedVersion) {
        throw new IllegalStateException("stale receipt version");
    }
    if (current.available() < units) {
        throw new IllegalStateException("insufficient stock");
    }
    return new Receipt(current.id(), current.tenant(),
        current.available() - units, current.version() + 1);
});''', language="java",
        proof="mutationUsesVersionAndDecrementsOnce, staleMutationReturnsErrorWithoutAnotherDebit and wrongTenantMutationDoesNotChangeTarget",
        cost="The local map update serializes writes per key within one process. It has no persistence, cross-node conflict control or database transaction. A conditional SQL update needs one round trip plus indexed row access; contention and retries depend on the target database.",
        mistakes=["Do not check the version in one query and update in a later unguarded query.", "Do not publish an event before confirming the mutation committed.", "Do not treat a test-supplied tenant context as authenticated identity."],
        related=["spring/tenant-versioned-write", "spring/graphql-tenant-read", "spring/outbox-atomic-write", "spring/kafka-outbox-handoff", "spring/graphql-error-boundary"]),
    dict(slug="graphql-error-boundary", section="spring/web-apis",
        title="Spring GraphQL errors: distinguish validation, resolver failure and nullable data",
        summary="GraphQL can return errors alongside data; schema nullability determines how far a failed field clears the result tree.",
        blocks=[
            ("Inspect both result channels", [
                "A document omitting the required limit argument fails schema validation before the list fetcher executes. A list request with limit 47 reaches the fetcher, which rejects it. Both return errors, but they are different failure stages. The checked schema marks receipts non-null, so the rejected fetcher clears root data. A cross-tenant nullable receipt lookup returns receipt: null without an error. Clients must not assume every null means the same thing.",
                "The fixture uses GraphQL Java's default exception handling and does not define a public error code or sanitization policy. A production GraphQL service should map known domain failures into stable public extensions and keep stack traces and internal values out of the response. [[spring/problem-details|REST ProblemDetail]] is a different transport shape; reuse domain categories, not the HTTP envelope."
            ]),
            ("Measure what the response hides", [
                "A successful HTTP status can still carry GraphQL errors. Transport tests should assert the JSON errors and data tree, and monitoring should count application failures separately from HTTP status. The source kit executes the schema directly, so it cannot establish deployed status codes, authentication errors, CORS or request-size controls."
            ]),
        ],
        code='''ExecutionResult rejected = source.graphQl().execute(
    ExecutionInput.newExecutionInput()
        .query("{ receipts(limit: 47) { id } }")
        .graphQLContext(Map.of("tenant", "north"))
        .build());
assertFalse(rejected.getErrors().isEmpty());
assertNull(rejected.getData());''', language="java",
        proof="missingRequiredArgumentIsRejectedBeforeFetcher, oversizedListRequestReturnsGraphQlError and tenantCannotReadAnotherTenantsReceipt",
        cost="Validation and execution both consume CPU; errors in non-null branches can discard otherwise useful selected data. The local test checks result structure, not network serialization, exception redaction or monitoring cardinality.",
        mistakes=["Do not inspect only the HTTP status when handling GraphQL failures.", "Do not assume a null field always indicates a resolver exception.", "Do not forward raw internal exception text as a public error policy."],
        related=["spring/graphql-schema-nullability", "spring/graphql-bounded-list", "spring/problem-details", "spring/graphql-service-tests", "spring/mvc-validation-problem"]),
    dict(slug="graphql-service-tests", section="spring/testing",
        title="Spring GraphQL service tests: stop short of claiming an HTTP endpoint",
        summary="Executing GraphQlSource directly checks schema and fetcher decisions without proving Boot wiring, filters, or transport behavior.",
        blocks=[
            ("Prove the small boundary precisely", [
                "GraphQlBoundaryContractTest builds an in-memory schema with GraphQlSource and registers data fetchers for receipt, receipts and reserve. Eight tests check selected fields, cross-tenant null, a bounded list, an oversized list error, a successful versioned mutation, stale mutation rejection, cross-tenant mutation denial and a missing required argument. Each test starts from fresh in-memory receipt values. No HTTP request, security filter, database or application component scan runs.",
                "The tenant value is installed directly in ExecutionInput. That is useful for resolver logic, but it cannot show whether a caller can forge context through headers or a GraphQL variable. A deployed test should start the real Boot web context, send authenticated requests to the GraphQL endpoint, verify interceptor mapping, then repeat against the target repository. [[spring/testing-boundaries|The broader test guide]] separates these layers."
            ]),
            ("Add failure tests that match the deployment", [
                "Before claiming production behavior, test persisted write races, nested-field authorization, query depth or cost limits, error redaction, request cancellation and batching under real data access. The service test provides a baseline for those integration checks; it does not substitute for them."
            ]),
        ],
        code='''ExecutionResult result = source.graphQl().execute(
    ExecutionInput.newExecutionInput()
        .query("mutation { reserve(id: \"RC-47\", units: 7, expectedVersion: 3) { available version } }")
        .graphQLContext(Map.of("tenant", "north"))
        .build());
assertTrue(result.getErrors().isEmpty());''', language="java",
        proof="all eight methods in GraphQlBoundaryContractTest, with no web server or datasource",
        cost="A direct schema test starts quickly and isolates field logic. Full web and database tests take longer but are required for authentication, serialization, request policy and concurrent persistence guarantees.",
        mistakes=["Do not treat GraphQlSource execution as proof that /graphql is deployed.", "Do not treat a manually injected tenant as a verified principal.", "Do not infer database atomicity from ConcurrentHashMap behavior."],
        related=["spring/testing-boundaries", "spring/graphql-tenant-read", "spring/graphql-optimistic-mutation", "spring/graphql-error-boundary", "spring/security-filter-chain"]),
]

titles = {path: row["title"] for path, row in by.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {"spring/web-apis": "spring-web", "spring/security": "spring-security",
            "spring/data-transactions": "spring-data", "spring/testing": "spring-testing"}
for index, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by, path
    assert all(target in titles for target in item["related"]), path
    body = p(item["summary"])
    for heading, paragraphs in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(p(text) for text in paragraphs)
    body += '<h2>Checked excerpt</h2><pre><code class="language-' + item["language"] + '">' + html.escape(item["code"].strip(), quote=False) + "</code></pre>"
    body += "<h2>Verification boundary</h2>" + p("The Java 21 / Spring Boot 4 source kit checks " + item["proof"] + ".")
    body += "<h2>Cost and limits</h2>" + p(item["cost"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(text) + "</li>" for text in item["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2>" + p(", ".join("[[" + target + "|" + titles[target] + "]]" for target in item["related"]) + ".")
    row = copy.deepcopy(by["spring/component-scan-vs-bean"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
        title=item["title"], summary=item["summary"], body=body, subject=subjects[item["section"]],
        tags=["spring", "spring-boot", "graphql", item["slug"]], sort_order=3700 + index,
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "framework_version": "Spring Boot 4.0.8 / Spring GraphQL 2.0.5",
        "java_version": "21 source-kit baseline", "verification_suite": "GraphQlBoundaryContractTest",
        "download_path": "/downloads/aitrove-spring-source-kit.zip",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    rows.append(row)
    by[path] = row

for section, label in [("spring/web-apis", "GraphQL schema and error decisions"),
                       ("spring/security", "GraphQL tenant boundaries"),
                       ("spring/data-transactions", "GraphQL data and mutation limits"),
                       ("spring/testing", "GraphQL test scope")]:
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by[section]
    hub["data"]["modules"].append({"title": label,
        "summary": "Check schema execution, authorization, costs and verification scope.", "lessons": paths})
    hub["body"] += "<h2>" + html.escape(label) + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths) + "</ul>"
    hub["updated_at"] = stamp

reverse = {
    "spring/tenant-receipt-authorization": ["spring/graphql-tenant-read"],
    "spring/tenant-versioned-write": ["spring/graphql-optimistic-mutation"],
    "spring/keyset-pagination": ["spring/graphql-bounded-list"],
    "spring/problem-details": ["spring/graphql-error-boundary"],
    "spring/testing-boundaries": ["spring/graphql-service-tests"],
    "spring/kafka-outbox-handoff": ["spring/graphql-optimistic-mutation"],
}
for path, targets in reverse.items():
    row = by[path]
    row["body"] += "<h2>GraphQL continuation</h2>" + p("Continue with " + ", ".join(
        "[[" + target + "|" + titles[target] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring GraphQL lessons and", len(reverse), "reverse-link groups")

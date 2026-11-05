"""Publish source-checked R2DBC lessons into the Spring umbrella."""

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
    dict(slug="r2dbc-subscription-boundary", section="spring/data-transactions",
        title="Spring R2DBC subscription boundary: constructing SQL does not execute it",
        summary="DatabaseClient returns a reactive publisher whose SQL work starts on subscription, so an unobserved publisher is an unperformed database operation.",
        blocks=[
            ("Keep the publisher connected to its caller", [
                "The fixture constructs an UPDATE publisher that would subtract seven units from SKU-47. Before subscribing, a separate query still sees 19 units. StepVerifier subscribes, observes one updated row, and the next query sees 12. Returning or composing that publisher is part of the command contract. Calling database.sql and discarding the resulting Mono does not schedule a write.",
                "The test uses block only in setup and assertions. A reactive request handler should return the pipeline instead of blocking its event-loop thread. Blocking JDBC, filesystem or remote calls inside a reactive chain can pin threads and erase the capacity benefit. [[spring/reactive-demand|Demand and subscription]] covers publisher semantics at the web boundary; [[spring/jdbc-template|JdbcTemplate]] is deliberately blocking."
            ]),
            ("Choose the data-access model consciously", [
                "R2DBC is not a transparent performance switch for a JDBC repository. Driver behavior, connection pools, transaction context, supported SQL features and debugging all need their own checks. If the service already performs blocking work on request threads and throughput is adequate, rewriting every repository to return Mono can add operational cost without solving a measured bottleneck. The source kit keeps the R2DBC fixture separate from its existing JDBC project."
            ]),
        ],
        code='''Mono<Long> debit = database.sql(
    "update stock_balance set available = available - :units "
        + "where sku = :sku and available >= :units")
    .bind("units", 7).bind("sku", "SKU-47")
    .fetch().rowsUpdated();
assertEquals(19, available());
StepVerifier.create(debit).expectNext(1L).verifyComplete();
assertEquals(12, available());''',
        proof="sqlPublisherDoesNotRunBeforeSubscription in the isolated reactive-r2dbc Maven project",
        cost="The test shows deferred execution, not higher throughput. Each subscribed operation still needs a database connection and SQL execution; pool capacity and database scheduling remain limits.",
        mistakes=["Do not construct a Mono and discard it while assuming the SQL ran.", "Do not call block on a reactive request thread.", "Do not assume switching APIs removes database contention."],
        related=["spring/reactive-demand", "spring/jdbc-template", "spring/r2dbc-bound-values", "spring/r2dbc-reactive-transaction", "spring/r2dbc-test-isolation"]),
    dict(slug="r2dbc-bound-values", section="spring/data-transactions",
        title="Spring R2DBC named binds: keep a receipt identifier out of SQL syntax",
        summary="DatabaseClient binds values through the driver so caller-supplied identifiers remain data rather than becoming executable SQL text.",
        blocks=[
            ("Bind values at the query boundary", [
                "The checked query asks for an SKU containing quote characters and an OR expression. With :sku bound as a value, it finds no row and leaves the real SKU-47 balance at 19. String concatenation would change the SQL text and create an injection path. Bind every input value, including tenant, ID, version, and amounts. Column or table names are different: they cannot be made safe by value binding; choose those from server-owned allowlists.",
                "The fixture uses an embedded H2 R2DBC driver. It proves that this query treats the hostile string as data. It does not establish that every SQL builder elsewhere is safe or that a production driver has identical query plans. [[spring/tenant-jdbc-predicate|The JDBC tenant predicate]] shows the same ownership requirement through a blocking API."
            ]),
            ("Do not over-read an empty result", [
                "The query uses one(), which yields no value when no row matches. The service layer still needs an explicit absent-row decision. A missing SKU, wrong tenant, and unavailable database should not all become the same successful empty response. Keep failure classification near the API boundary and do not log untrusted raw SQL fragments."
            ]),
        ],
        code='''Mono<Integer> found = database.sql(
    "select available from stock_balance where sku = :sku")
    .bind("sku", "SKU-47' or '1'='1")
    .map((row, metadata) -> row.get("available", Integer.class))
    .one();
StepVerifier.create(found).verifyComplete();''',
        proof="boundIdentifierIsDataRatherThanSql in the isolated reactive-r2dbc Maven project",
        cost="Binding has a small driver cost but avoids reparsing attacker-controlled SQL text and supports plan reuse where the database permits it. The real cost is the indexed lookup and connection acquisition, not the string validation example.",
        mistakes=["Do not concatenate caller input into SQL text.", "Do not expect bind markers to parameterize table or column names.", "Do not confuse an empty result with a database error."],
        related=["spring/r2dbc-subscription-boundary", "spring/tenant-jdbc-predicate", "spring/r2dbc-versioned-write", "spring/graphql-tenant-read", "spring/jdbc-template"]),
    dict(slug="r2dbc-reactive-transaction", section="spring/data-transactions",
        title="Spring R2DBC reactive transaction: roll back the event marker with a rejected debit",
        summary="TransactionalOperator can bind multiple R2DBC publishers to one reactive transaction and roll them back when the composed pipeline fails.",
        blocks=[
            ("Compose both writes before applying the operator", [
                "The fixture inserts EVT-47 into applied_reservation, then executes a conditional stock debit in the same reactive chain. TransactionalOperator wraps the chain. On success, the marker exists and SKU-47 moves from 19 to 12 with version 4. If a 20-unit debit affects zero rows, the pipeline converts that result into an error; the marker rolls back and stock stays at 19. [[spring/consumer-idempotency|The consumer ledger]] explains why the marker and mutation must share a commit.",
                "This uses R2dbcTransactionManager and one R2DBC ConnectionFactory. A JDBC TransactionTemplate in a different datasource does not automatically join the reactive transaction. Reactor Context carries the transaction association through the subscribed pipeline; splitting work into an unmanaged subscribe call can lose that boundary. [[spring/transactions|The JDBC transaction lesson]] is a separate model."
            ]),
            ("Specify the failure policy", [
                "An error signal triggers rollback here. A caught exception converted to a normal value can instead lead to commit. The method therefore turns a zero-row update into Mono.error rather than swallowing it. Cancellation, timeout, and retry semantics need tests against the selected driver and production database; this embedded fixture checks two sequential outcomes only."
            ]),
        ],
        code='''return database.sql("insert into applied_reservation(event_id) values (:eventId)")
    .bind("eventId", eventId).fetch().rowsUpdated()
    .then(database.sql(
        "update stock_balance set available = available - :units, version = version + 1 "
            + "where sku = :sku and tenant = :tenant "
            + "and version = :expectedVersion and available >= :units")
        .bind("units", units).bind("sku", sku).bind("tenant", tenant)
        .bind("expectedVersion", expectedVersion).fetch().rowsUpdated())
    .flatMap(changed -> changed == 1 ? Mono.<Void>empty()
        : Mono.error(new IllegalStateException("reservation rejected")))
    .as(transactions::transactional);''',
        proof="transactionCommitsMarkerAndVersionedDebitTogether and transactionRollsBackMarkerAfterRejectedDebit",
        cost="One transaction holds a connection until completion and adds an indexed marker write. Long reactive chains inside the transaction can hold database resources for too long; keep remote calls and slow work outside the database commit window.",
        mistakes=["Do not put the marker outside the transactional pipeline.", "Do not convert a failed row count into a normal completion if rollback is required.", "Do not assume a JDBC transaction joins a R2DBC transaction automatically."],
        related=["spring/r2dbc-versioned-write", "spring/consumer-idempotency", "spring/transactions", "spring/transaction-propagation", "spring/r2dbc-test-isolation"]),
    dict(slug="r2dbc-versioned-write", section="spring/data-transactions",
        title="Spring R2DBC conditional update: test tenant, version and stock floor in one statement",
        summary="A reactive stock reservation should let the database decide whether one row satisfies tenant, version and availability constraints.",
        blocks=[
            ("Use the affected-row count as the decision", [
                "The checked UPDATE includes SKU, tenant, expected version and available >= units in its predicate. A matching reservation changes one row. A stale version or wrong tenant changes zero rows, and the surrounding transaction rolls back the inserted event marker. A separate SELECT followed by an unguarded UPDATE would reopen the race that the predicate closes. [[spring/tenant-versioned-write|The JDBC counterpart]] uses the same invariant with a different client API.",
                "Zero rows does not explain which predicate failed. Returning distinct wrong-tenant and stale-version details without care can reveal whether another tenant owns a row. Decide what the caller may learn, then log the internal reason only where authorized. The test checks state; it does not define a deployed HTTP or GraphQL error envelope."
            ]),
            ("Retry a complete command only when safe", [
                "A stale client may re-read and resubmit a new command; a transient database error may justify retrying the original command. Do not blindly retry a stale version with the same expectation. Stable event identity and a unique marker protect repeated delivery of the same committed command, but they do not decide whether a newly calculated reservation is valid."
            ]),
        ],
        code='''database.sql("update stock_balance set available = available - :units, "
        + "version = version + 1 where sku = :sku and tenant = :tenant "
        + "and version = :expectedVersion and available >= :units")
    .bind("units", units).bind("sku", sku).bind("tenant", tenant)
    .bind("expectedVersion", expectedVersion)
    .fetch().rowsUpdated();''',
        proof="transactionCommitsMarkerAndVersionedDebitTogether, staleVersionRollsBackEventMarker and wrongTenantRollsBackEventMarker",
        cost="A primary-key lookup with a conditional update is bounded by the matching row and its indexes, but concurrent writers can contend on that row. The embedded H2 result does not prove target-database locking, retry or isolation behavior.",
        mistakes=["Do not check version and stock in separate unguarded statements.", "Do not infer the exact failure reason from a zero-row count alone.", "Do not retry a stale business command without revisiting its intent."],
        related=["spring/tenant-versioned-write", "spring/r2dbc-reactive-transaction", "spring/graphql-optimistic-mutation", "spring/consumer-idempotency", "spring/transaction-isolation-choice"]),
    dict(slug="r2dbc-test-isolation", section="spring/testing",
        title="Spring R2DBC fixture isolation: keep incompatible H2 versions out of one test classpath",
        summary="An embedded reactive database test must use a driver and database engine version that agree at the binary API level.",
        blocks=[
            ("Make the dependency boundary visible", [
                "The main Spring source kit pins H2 2.3.232 for long-standing JDBC examples. Boot 4.0.8 manages r2dbc-h2 1.1.0.RELEASE with H2 2.4.240. Placing the reactive driver on the original test classpath produced a NoSuchMethodError before any SQL ran. The fixture now lives in reactive-r2dbc, a separate Maven project inside the same download, so its managed H2 pair can be tested without changing earlier JDBC results. This is a binary compatibility finding, not a reason to silently bump the entire course's database baseline.",
                "Run mvn test in both directories. The reactive project has six H2 checks for subscription timing, value binding, commit, rollback, stale version and wrong tenant. Its direct DatabaseClient calls do not start Boot, WebFlux or a connection pool. [[spring/testing-boundaries|The testing guide]] explains why passing those local checks cannot establish deployment behavior."
            ]),
            ("Promote the actual database contract separately", [
                "Production databases differ in locking, isolation, statement timeout, connection cleanup and error translation. Re-run the conditional update and rollback cases against the intended engine with concurrent sessions. Check cancellation while a transaction is open, and measure pool saturation under load. The isolated H2 test is a fast contract probe, not a production certification."
            ]),
        ],
        code='''<dependency>
  <groupId>org.springframework</groupId>
  <artifactId>spring-r2dbc</artifactId>
</dependency>
<dependency>
  <groupId>io.r2dbc</groupId>
  <artifactId>r2dbc-h2</artifactId>
</dependency>''',
        proof="all six methods in the nested reactive-r2dbc Maven project; the main source-kit tests run on their existing JDBC dependency graph",
        cost="Two small Maven projects require two test commands and a larger source download. That cost is explicit and avoids a misleading green suite assembled from incompatible H2 libraries.",
        mistakes=["Do not hide a NoSuchMethodError by skipping reactive tests.", "Do not upgrade the JDBC fixture's database without rechecking its published examples.", "Do not treat embedded H2 behavior as proof of production database concurrency."],
        related=["spring/r2dbc-subscription-boundary", "spring/r2dbc-reactive-transaction", "spring/testing-boundaries", "spring/transaction-isolation-choice", "spring/jdbc-template"]),
]

titles = {path: row["title"] for path, row in by.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {"spring/data-transactions": "spring-data", "spring/testing": "spring-testing"}
for index, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by, path
    assert all(target in titles for target in item["related"]), path
    body = p(item["summary"])
    for heading, paragraphs in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(p(text) for text in paragraphs)
    body += '<h2>Checked excerpt</h2><pre><code class="language-' + ("xml" if item["slug"] == "r2dbc-test-isolation" else "java") + '">' + html.escape(item["code"].strip(), quote=False) + "</code></pre>"
    body += "<h2>Verification boundary</h2>" + p("The Java 21 / Spring Boot 4 source kit checks " + item["proof"] + ".")
    body += "<h2>Cost and limits</h2>" + p(item["cost"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(text) + "</li>" for text in item["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2>" + p(", ".join("[[" + target + "|" + titles[target] + "]]" for target in item["related"]) + ".")
    row = copy.deepcopy(by["spring/component-scan-vs-bean"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
        title=item["title"], summary=item["summary"], body=body, subject=subjects[item["section"]],
        tags=["spring", "spring-boot", "r2dbc", item["slug"]], sort_order=3750 + index,
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "framework_version": "Spring Boot 4.0.8 / Spring Framework 7 R2DBC",
        "java_version": "21 source-kit baseline", "verification_suite": "reactive-r2dbc: R2dbcBoundaryContractTest",
        "download_path": "/downloads/aitrove-spring-source-kit.zip",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    rows.append(row)
    by[path] = row

for section, label in [("spring/data-transactions", "R2DBC subscription and transaction contracts"),
                       ("spring/testing", "R2DBC dependency and test scope")]:
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by[section]
    hub["data"]["modules"].append({"title": label,
        "summary": "Check subscription, binding, rollback and fixture dependency scope.", "lessons": paths})
    hub["body"] += "<h2>" + html.escape(label) + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths) + "</ul>"
    hub["updated_at"] = stamp

reverse = {
    "spring/transactions": ["spring/r2dbc-reactive-transaction"],
    "spring/jdbc-template": ["spring/r2dbc-subscription-boundary", "spring/r2dbc-bound-values"],
    "spring/tenant-versioned-write": ["spring/r2dbc-versioned-write"],
    "spring/consumer-idempotency": ["spring/r2dbc-reactive-transaction"],
    "spring/reactive-demand": ["spring/r2dbc-subscription-boundary"],
    "spring/testing-boundaries": ["spring/r2dbc-test-isolation"],
    "spring/graphql-optimistic-mutation": ["spring/r2dbc-versioned-write"],
}
for path, targets in reverse.items():
    row = by[path]
    row["body"] += "<h2>Reactive database continuation</h2>" + p("Continue with " + ", ".join(
        "[[" + target + "|" + titles[target] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring R2DBC lessons and", len(reverse), "reverse-link groups")

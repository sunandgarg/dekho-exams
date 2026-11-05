"""Add original Spring Kafka contract lessons to the Spring umbrella."""

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


def paragraph(text):
    escaped = html.escape(text)
    return "<p>" + re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>", escaped,
    ) + "</p>"


lessons = [
    dict(
        slug="kafka-listener-manual-ack", section="spring/production",
        title="Spring Kafka manual acknowledgement: commit work before advancing the offset",
        summary="A listener can acknowledge a record only after its local database operation finishes, but a broker offset and database commit remain separate events.",
        blocks=[
            ("Place the acknowledgement after the write", [
                "The checked listener accepts a stock reservation, opens a database transaction, inserts a stable event ID and conditionally debits one SKU. It calls acknowledge only after the transaction callback returns. If the debit fails, the method throws and the test observes no acknowledgement. The event marker rolls back with the debit. [[spring/consumer-idempotency|The event ledger]] is what makes a later delivery safe to inspect again.",
                "Manual acknowledgement is a container setting, not a method parameter that changes consumer behavior by itself. The listener names a manualAckKafkaListenerContainerFactory; the fixture also checks a factory configured with MANUAL_IMMEDIATE. An actual application must register that named factory with compatible deserializers and a consumer group. A method invoked directly in a unit test does not prove that a Kafka container loaded it or committed an offset."
            ]),
            ("Draw the failure cut points", [
                "A process can commit the database transaction and stop before acknowledging. Kafka may then redeliver the same event. The event-ID constraint prevents a second debit, after which the listener may acknowledge the duplicate. If the acknowledgement succeeds but a separate downstream side effect fails, that side effect has no retry guarantee from this offset. Put such work behind its own durable boundary. [[spring/outbox-atomic-write|The outbox write]] covers one database commit; [[spring/kafka-outbox-handoff|the Kafka handoff]] still needs replay handling."
            ]),
        ],
        code='''@KafkaListener(topics = "stock-reservations", groupId = "stock-ledger-v1",
    containerFactory = "manualAckKafkaListenerContainerFactory")
public void receive(ConsumerRecord<String, StockReservation> record,
                    Acknowledgment acknowledgment) {
    StockReservation reservation = record.value();
    if (reservation == null || record.key() == null
            || !record.key().equals(reservation.sku())) {
        throw new IllegalArgumentException("record key and reservation SKU differ");
    }
    try {
        transactions.executeWithoutResult(status -> {
            jdbc.update("insert into applied_reservation(event_id, sku, units) values (?, ?, ?)",
                reservation.eventId(), reservation.sku(), reservation.units());
            int updated = jdbc.update(
                "update stock_balance set available = available - ? where sku = ? and available >= ?",
                reservation.units(), reservation.sku(), reservation.units());
            if (updated != 1) throw new IllegalStateException("stock item absent or insufficient");
        });
    } catch (DuplicateKeyException duplicate) {
        var recorded = jdbc.queryForMap(
            "select sku, units from applied_reservation where event_id = ?", reservation.eventId());
        if (!reservation.sku().equals(recorded.get("SKU"))
                || reservation.units() != ((Number) recorded.get("UNITS")).intValue()) {
            throw new IllegalStateException("event ID reused for a different reservation", duplicate);
        }
    }
    acknowledgment.acknowledge();
}''',
        proof="acknowledgesOnlyAfterCommittedStockChange and insufficientStockRollsBackMarkerAndDoesNotAcknowledge; listenerDeclaresManualAcknowledgmentContainerAndStableGroup checks annotation and factory settings",
        cost="Each record incurs a database transaction and at least an event-ID index write. Throughput depends on partition count, database contention and acknowledgement policy. The source kit runs no broker, so it cannot establish redelivery timing, rebalance behavior or offset durability.",
        mistakes=["Do not infer manual acknowledgement from the presence of an Acknowledgment argument alone.", "Do not acknowledge before the business transaction commits.", "Do not call this an atomic Kafka-and-JDBC transaction."],
        related=["spring/consumer-idempotency", "spring/transaction-propagation", "spring/outbox-atomic-write", "spring/kafka-idempotent-consumer", "spring/kafka-testing-layers"],
    ),
    dict(
        slug="kafka-idempotent-consumer", section="spring/data-transactions",
        title="Spring Kafka duplicate delivery: let a unique event ID decide the second debit",
        summary="A database uniqueness constraint can make one local stock mutation safe under repeated delivery of the same event ID.",
        blocks=[
            ("Reject repetition inside the transaction", [
                "The fixture stores EVT-47 with its SKU and unit count in applied_reservation, then changes SKU-47 from 19 to 12 in one transaction. Calling the listener again with the same event ID hits the primary key. It acknowledges a replay only after checking the stored SKU and amount; a conflicting replay remains unacknowledged. No preflight SELECT makes the initial decision: two concurrent consumers could both observe absence before either inserts. [[spring/consumer-dedup-transaction|The database ledger lesson]] explains the same ownership rule without a Kafka method around it.",
                "A failure after marker insertion but before the stock update rolls the marker back. In the checked insufficient-stock case, the available value stays 19 and the applied-event count stays zero. The listener leaves the record unacknowledged so the container error policy can decide what happens next. Repeating that record forever would not create stock; [[spring/kafka-retry-and-poison|failure classification]] needs an explicit policy."
            ]),
            ("Scope the key to the real event identity", [
                "The fixture uses one global event-ID primary key. A multi-tenant service may need a composite tenant-and-event identity, plus validation that the authenticated event source is allowed to affect that tenant. A reused event ID with different payload is a conflict worth recording, not automatically proof that the second payload is harmless. Retain the marker at least as long as the system can redeliver the event."
            ]),
        ],
        code='''transactions.executeWithoutResult(status -> {
    jdbc.update("insert into applied_reservation(event_id, sku, units) values (?, ?, ?)",
        reservation.eventId(), reservation.sku(), reservation.units());
    int updated = jdbc.update(
        "update stock_balance set available = available - ? where sku = ? and available >= ?",
        reservation.units(), reservation.sku(), reservation.units());
    if (updated != 1) throw new IllegalStateException("stock item absent or insufficient");
});''',
        proof="acknowledgesDuplicateWithoutSecondDebit, conflictingDuplicateIsNotAcknowledged and insufficientStockRollsBackMarkerAndDoesNotAcknowledge",
        cost="The event marker adds one indexed row per retained event, so storage and retention need capacity planning. The local H2 test calls the listener sequentially. Concurrent inserts, deadlocks, isolation and constraint translation must be checked on the production database.",
        mistakes=["Do not use a read-before-write check as the only duplicate guard.", "Do not commit the marker in a different transaction from the stock mutation.", "Do not discard marker rows while old records can still return."],
        related=["spring/kafka-listener-manual-ack", "spring/consumer-idempotency", "spring/transaction-isolation-choice", "spring/kafka-retry-and-poison", "spring/kafka-partition-key"],
    ),
    dict(
        slug="kafka-partition-key", section="spring/production",
        title="Spring Kafka record keys: preserve per-SKU order without claiming global order",
        summary="A stable record key gives a producer a consistent partitioning input; ordering is a property of records within one partition, not of the whole topic.",
        blocks=[
            ("Key by the state that must stay ordered", [
                "The publisher sends a stock reservation with SKU-47 as its key. The listener rejects a record whose key names a different SKU than the payload. That check catches one category of routing corruption before a database write. It does not prove that every same-SKU record will remain in the same partition forever: changing partition counts or partitioner configuration can change placement. The source-kit test checks the method argument and rejection path, not broker partition assignment.",
                "A tenant-scoped stock table should use a tenant-aware key or an explicit ordering design; two tenants may both use SKU-47. Choose the key from the domain aggregate whose concurrent operations must serialize, then record the partitioning contract in the producer and consumer tests. [[spring/tenant-versioned-write|A conditional versioned write]] is still needed if multiple workers can race in the database."
            ]),
            ("Plan for throughput and skew", [
                "One extremely busy SKU can become a hot partition. More consumers in the same group do not split one partition's ordered stream across those consumers. If the application needs higher throughput, decide whether the aggregate can be subdivided without losing its invariant; do not quietly randomize keys and hope the database repairs ordering. [[spring/kafka-idempotent-consumer|Deduplication]] handles repeats, not the semantic order of two different updates."
            ]),
        ],
        code='''CompletableFuture<SendResult<String, StockReservation>> publish(
        StockReservation reservation) {
    return operations.send("stock-reservations", reservation.sku(), reservation);
}''',
        proof="publisherUsesSkuAsPartitionKeyAndReturnsSendCompletion and mismatchedKeyIsRejectedBeforeDatabaseWork",
        cost="A hot key limits parallel work for that aggregate and can raise consumer lag. The local fixture has no broker or partitioner, so actual partition placement, reassignment and ordering under retries remain integration-test work.",
        mistakes=["Do not describe partition order as global topic order.", "Do not choose a random key for operations that require per-aggregate sequencing.", "Do not assume a stable key survives partition-count changes with identical placement."],
        related=["spring/kafka-producer-completion", "spring/kafka-idempotent-consumer", "spring/tenant-versioned-write", "spring/kafka-testing-layers"],
    ),
    dict(
        slug="kafka-producer-completion", section="spring/production",
        title="Spring Kafka producer future: observe broker send completion separately from command success",
        summary="KafkaOperations.send returns a future, so a caller must observe completion or failure instead of treating the method call as delivery evidence.",
        blocks=[
            ("Return the completion signal", [
                "The small publisher returns the future from KafkaOperations.send. Its checked success path verifies the topic, key and reservation passed to the API. Its failure path supplies a failed future and confirms that the caller still sees a failure when joining it. Neither check starts a broker. A completed mock future only proves that the gateway did not discard the signal.",
                "A successful producer completion is narrower than an end-to-end business result. It does not say that a consumer ran, wrote its database, or sent a later notification. The exact broker durability meaning depends on producer acknowledgements and broker configuration. If an HTTP request cannot afford to wait, [[spring/outbox-atomic-write|record the intent]] in the local transaction and hand delivery to a relay. Do not turn fire-and-forget into an implicit success response."
            ]),
            ("Keep retries tied to one event identity", [
                "A timed-out send may have reached Kafka even when the caller did not observe its result. Reusing the same event ID on a retry lets the consumer reject a duplicate. Generating a fresh ID for every attempt defeats that guard. [[spring/kafka-idempotent-consumer|The event ledger]] closes that local mutation gap; [[spring/kafka-outbox-handoff|the relay cut points]] explain the producer side."
            ]),
        ],
        code='''CompletableFuture<SendResult<String, StockReservation>> publish(
        StockReservation reservation) {
    return operations.send("stock-reservations", reservation.sku(), reservation);
}''',
        proof="publisherUsesSkuAsPartitionKeyAndReturnsSendCompletion and failedSendRemainsFailedForCallerToHandle; the checked gateway returns the future directly",
        cost="Waiting on a future adds broker round-trip latency to the caller. An asynchronous callback needs bounded execution and durable retry ownership if delivery matters. The fixture measures neither broker latency nor acknowledgement durability.",
        mistakes=["Do not mark a command delivered immediately after calling send.", "Do not lose an exceptional completion in an unobserved future.", "Do not regenerate event identity for an uncertain retry."],
        related=["spring/kafka-partition-key", "spring/kafka-outbox-handoff", "spring/outbox-atomic-write", "spring/async-future-failure"],
    ),
    dict(
        slug="kafka-retry-and-poison", section="spring/production",
        title="Spring Kafka listener failures: separate transient retries from poison records",
        summary="A failed listener invocation needs a bounded error policy, because an unacknowledged record alone does not decide retry or recovery.",
        blocks=[
            ("Classify the rejection", [
                "The local listener throws before acknowledging when the key disagrees with the payload, and it throws after a rolled-back transaction when stock is insufficient. Those are different failures. A mismatched key is unlikely to improve with time; a database outage may. Spring Kafka's container error handler can apply bounded backoff and a recovery destination, but the source kit deliberately does not register one or run a broker. The checked assertion is only that the method left the record unacknowledged.",
                "Define what a recovered record means operationally: topic, original event ID, reason category, attempt count, and a way to inspect or replay it. A dead-letter publication can fail too. If the recovery handler returns success before a durable recovery record exists, the consumer can lose work. [[spring/kafka-testing-layers|A broker integration test]] must check offset movement, recovery publication and restart behavior."
            ]),
            ("Do not retry a business rejection forever", [
                "The checked stock update requires available units. A reservation for 20 units against 19 fails and rolls back its event marker. Retrying that exact record indefinitely monopolizes a partition unless a later inventory change is intentionally part of the business contract. Decide whether to reject it, park it, or keep it pending with a deadline. The failure policy is a product rule with an operator path, not just a backoff number."
            ]),
        ],
        code='''int updated = jdbc.update(
    "update stock_balance set available = available - ? where sku = ? and available >= ?",
    reservation.units(), reservation.sku(), reservation.units());
if (updated != 1) throw new IllegalStateException("stock item absent or insufficient");''',
        proof="insufficientStockRollsBackMarkerAndDoesNotAcknowledge and mismatchedKeyIsRejectedBeforeDatabaseWork; broker retry and dead-letter behavior are not locally verified",
        cost="A long retry interval delays records behind the failing record in its partition; very short retries can amplify load on an unhealthy database. The correct bound depends on service latency, retention and operator recovery time. No broker policy or dead-letter topic is tested here.",
        mistakes=["Do not treat every exception as transient.", "Do not assume lack of acknowledgement alone defines a finite retry policy.", "Do not acknowledge a poison record before durable recovery if loss is unacceptable."],
        related=["spring/kafka-listener-manual-ack", "spring/kafka-testing-layers", "spring/consumer-idempotency", "spring/relay-retry-schedule"],
    ),
    dict(
        slug="kafka-outbox-handoff", section="spring/data-transactions",
        title="Spring outbox to Kafka: name the crash window between send and relay acknowledgement",
        summary="A database outbox protects the command write, while an uncertain Kafka send requires replay with a stable event ID.",
        blocks=[
            ("One database commit; two delivery outcomes", [
                "The existing receipt command stores business state and an outbox row in one database transaction. A separate relay claims that row and sends a Kafka record. If the send fails before broker acceptance, the relay can retry. If Kafka accepts it and the relay crashes before marking the row delivered, a retry may publish it again. No ordering of these two independent commits erases both crash windows. [[spring/outbox-fenced-ack|A fenced relay acknowledgement]] limits stale workers; [[spring/kafka-idempotent-consumer|the event ledger]] limits repeated stock mutation.",
                "The fixture's producer future is observed. It is not connected to the outbox H2 tests as an end-to-end process, and there is no Kafka broker in the kit. A production relay still needs serialization, headers or schema versioning, bounded retry, lease renewal, metrics and a recovery queue for non-retryable records. [[spring/outbox-relay-service-project|The relay project]] describes those operational states."
            ]),
            ("Preserve event identity through every attempt", [
                "The outbox row should carry a durable event ID and payload version. Every retry sends that same identity. If an editor or a worker recomputes payload from mutable current database state, the repeated event may no longer represent the command that originally committed. Store enough data to reproduce the intended event or define an explicit projection contract."
            ]),
        ],
        code='''// The checked gateway exposes completion; the relay must not mark a row delivered
// until it has decided what this completion means for its retry policy.
CompletableFuture<SendResult<String, StockReservation>> sent =
    operations.send("stock-reservations", reservation.sku(), reservation);''',
        proof="failedSendRemainsFailedForCallerToHandle plus the source kit's existing H2 outbox and consumer-ledger tests; a combined outbox-to-Kafka relay is not present",
        cost="The outbox adds a durable row, claim query, retention work and at least one extra delivery step. It trades a single-request send for eventual delivery with observable lag; broker acceptance and database acknowledgement still need a crash-recovery integration test.",
        mistakes=["Do not mark an outbox row delivered before examining the send completion.", "Do not claim a database commit and broker send are one atomic transaction.", "Do not assign a new event ID to every relay attempt."],
        related=["spring/outbox-atomic-write", "spring/outbox-fenced-ack", "spring/outbox-relay-service-project", "spring/kafka-producer-completion", "spring/kafka-idempotent-consumer"],
    ),
    dict(
        slug="kafka-testing-layers", section="spring/testing",
        title="Spring Kafka testing layers: know what a direct listener test cannot prove",
        summary="Direct method calls check application decisions, while serialization, group assignment, offsets and redelivery require a running broker.",
        blocks=[
            ("Keep each assertion at its layer", [
                "KafkaBoundaryContractTest calls the listener with a ConsumerRecord and a mock Acknowledgment. It checks a committed debit, duplicate event ID, conflicting replay, failed debit rollback, key mismatch, producer send arguments and a failed future. It also reflects on the listener annotation and configures a manual-ack factory object. These tests are fast, deterministic checks of local code. They do not start a Kafka listener container, deserialize bytes or commit an offset.",
                "A container-level test should register the actual factory, serializers, error handler and listener bean against a disposable broker. It should publish a record, observe the committed business row, force a restart after the database commit but before acknowledgement, and verify that the same event ID does not debit twice. Add a poison record and check recovery publication plus offset movement. [[spring/testing-boundaries|The general testing boundary]] warns against claiming deployment behavior from a narrow fixture."
            ]),
            ("Promote the real configuration to the test", [
                "Do not build one factory in the test and a different one in production. The fixture's factory assertion checks MANUAL_IMMEDIATE as an API setting but does not register it under the listener's named containerFactory. Wire that exact bean in the integration environment, use the deployed deserializer and schema version, then test with the target database engine if correctness depends on its constraint or locking behavior."
            ]),
        ],
        code='''@Test
void insufficientStockRollsBackMarkerAndDoesNotAcknowledge() {
    Acknowledgment acknowledgment = mock(Acknowledgment.class);
    assertThrows(IllegalStateException.class,
        () -> consumer.receive(record("EVT-48", "SKU-47", 20), acknowledgment));
    verifyNoInteractions(acknowledgment);
    assertEquals(19, available());
    assertEquals(0, appliedCount());
}''',
        proof="all eight methods in KafkaBoundaryContractTest, running without a broker",
        cost="Direct tests run quickly but leave infrastructure behavior unobserved. Broker and production-database tests cost more startup time and resources; reserve them for the guarantees that require those components, especially offset recovery, partition assignment and concurrent deduplication.",
        mistakes=["Do not treat a direct method call as proof of container registration.", "Do not treat a mock send completion as proof of Kafka acceptance.", "Do not omit restart and poison-record checks before promising at-least-once recovery."],
        related=["spring/kafka-listener-manual-ack", "spring/kafka-producer-completion", "spring/kafka-retry-and-poison", "spring/testing-boundaries", "spring/consumer-idempotency"],
    ),
]

titles = {path: row["title"] for path, row in by.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
for item in lessons:
    path = "spring/" + item["slug"]
    assert path not in by, path
    assert all(target in titles for target in item["related"]), path
    body = paragraph(item["summary"])
    for heading, paragraphs in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(paragraph(text) for text in paragraphs)
    body += '<h2>Code boundary</h2><pre><code class="language-java">' + html.escape(item["code"].strip(), quote=False) + "</code></pre>"
    body += "<h2>Verification boundary</h2>" + paragraph("The Java 21 / Spring Boot 4 source kit checks " + item["proof"] + ".")
    body += "<h2>Cost and limits</h2>" + paragraph(item["cost"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(text) + "</li>" for text in item["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(", ".join("[[" + target + "|" + titles[target] + "]]" for target in item["related"]) + ".")
    row = copy.deepcopy(by["spring/component-scan-vs-bean"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=item["title"], summary=item["summary"], body=body,
               subject={"spring/production": "spring-production", "spring/data-transactions": "spring-data", "spring/testing": "spring-testing"}[item["section"]],
               tags=["spring", "spring-boot", "kafka", item["slug"]], sort_order=2500 + len(rows),
               published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "framework_version": "Spring Boot 4.0.8 / Spring Kafka 4.0.7",
        "java_version": "21 source-kit baseline", "verification_suite": "KafkaBoundaryContractTest",
        "download_path": "/downloads/aitrove-spring-source-kit.zip",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by[path] = row

for section, label in [("spring/production", "Kafka delivery boundaries"), ("spring/data-transactions", "Kafka and database ownership"), ("spring/testing", "Kafka verification layers")]:
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by[section]
    hub["data"]["modules"].append({"title": label, "summary": "Trace producer, consumer and recovery cut points without treating local tests as broker evidence.", "lessons": paths})
    hub["body"] += "<h2>" + html.escape(label) + "</h2><ul>" + "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths) + "</ul>"
    hub["updated_at"] = stamp

reverse = {
    "spring/consumer-idempotency": ["spring/kafka-idempotent-consumer", "spring/kafka-listener-manual-ack"],
    "spring/outbox-atomic-write": ["spring/kafka-outbox-handoff"],
    "spring/outbox-relay-service-project": ["spring/kafka-outbox-handoff", "spring/kafka-producer-completion"],
    "spring/testing-boundaries": ["spring/kafka-testing-layers"],
    "spring/async-future-failure": ["spring/kafka-producer-completion"],
    "spring/transaction-isolation-choice": ["spring/kafka-idempotent-consumer"],
}
for path, targets in reverse.items():
    row = by[path]
    row["body"] += "<h2>Kafka continuation</h2>" + paragraph("Continue with " + ", ".join("[[" + target + "|" + titles[target] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring Kafka lessons and", len(reverse), "reverse-link groups")

"""Extend Spring Batch and Modulith coverage with checked failure boundaries."""

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


def paragraph(value):
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>", escaped) + "</p>"


lessons = [
    dict(slug="batch-skip-limit-check", section="spring/production", family="batch", checked=True,
        title="Spring Batch skip limits: the next invalid receipt fails the step",
        summary="A skip budget counts rejected items across a fault-tolerant step; the next eligible error beyond the limit fails the execution.",
        blocks=[("Keep the rejected row visible",
            "The checked import reads receipts with IDs 1 through 4. A negative unit count at ID 2 is rejected by the processor. With a skip limit of one, IDs 1, 3 and 4 reach the target table and the step reports one skip. This is a business decision, not a data-cleaning convenience: a money-moving import may require zero skips and an operator review instead. [[spring/batch-retry-skip-policy|The policy lesson]] separates deterministic input errors from temporary faults."),
            ("Fail on the next bad row",
            "A second run contains bad values at IDs 2 and 3. ID 1 commits, the first invalid row consumes the single skip, and the second invalid row makes the job FAILED. Its target has one row. The failure does not remove an earlier committed chunk. [[spring/batch-committed-chunk|The chunk test]] shows the same commit boundary without skip configuration."),
            ("Reconcile before calling a job complete",
            "A COMPLETED status with one skip is not proof that four expected receipts were accepted. Record the manifest identity, accepted IDs and rejected IDs in a reviewable result. The source kit checks counts but does not persist a quarantine table or an operator approval workflow.")],
        code='.faultTolerant()\n.skip(InvalidReceiptException.class).skipLimit(1)\n.retry(TemporaryReceiptException.class).retryLimit(2)',
        cost="Skipping reduces successful output and may require a second correction run. The step tracks skip counts; storing rejected payloads safely adds disk and privacy costs.",
        mistakes=["Do not describe a completed job with skipped receipts as a full import.", "Do not raise the skip limit to hide an unknown data defect.", "Do not treat a committed earlier chunk as rolled back when a later skip budget fails."],
        related=["spring/batch-retry-skip-policy", "spring/batch-retry-exhaustion", "spring/batch-committed-chunk", "spring/batch-job-identity"]),
    dict(slug="batch-retry-exhaustion", section="spring/production", family="batch", checked=True,
        title="Spring Batch retry exhaustion: a temporary error needs a finite stop",
        summary="Retryable processing errors can be attempted again, but exhausting the configured limit leaves the job failed.",
        blocks=[("Prove recovery and exhaustion separately",
            "In one checked run, receipt ID 3 fails processing once with TemporaryReceiptException, succeeds on a later attempt, and the job finishes with three accepted rows after one invalid row was skipped. Another run forces the temporary exception on every attempt. Its job status is FAILED and its target remains empty because the two-row chunk never commits."),
            ("Bound work at the right layer",
            "The local fixture uses retryLimit(2) for the processor exception. A production import also needs a wall-clock deadline and backoff suited to its database, because a service-wide outage can make a fleet of workers retry at once. [[spring/cloud-client-retry|Client retry]] and Batch retry should share an attempt budget when a processor calls a remote service."),
            ("Preserve a stable write decision",
            "A retried processor or writer can run more than once; avoid irreversible side effects inside either. The earlier [[spring/batch-idempotent-writer|writer lesson]] uses a source key to tolerate replay. This test uses in-memory H2 and a processor exception; it does not prove deadlock recovery against a production database.")],
        code='.faultTolerant()\n.retry(TemporaryReceiptException.class).retryLimit(2)\n.skip(InvalidReceiptException.class).skipLimit(1)',
        cost="Every extra attempt repeats processing and can extend lock time. Bound both attempts and elapsed time before retrying shared infrastructure.",
        mistakes=["Do not retry a deterministic negative-unit input.", "Do not assume a retryable classification means the fault will eventually clear.", "Do not put a non-idempotent remote write inside retryable processing."],
        related=["spring/batch-skip-limit-check", "spring/batch-idempotent-writer", "spring/cloud-client-retry", "spring/batch-job-identity"]),
    dict(slug="batch-result-reconciliation", section="spring/production", family="batch", checked=False,
        title="Spring Batch reconciliation: report accepted and rejected receipt IDs",
        summary="A job result needs business counts and source identities alongside its framework status when skips are permitted.",
        blocks=[("Define the accounting equation",
            "For a fixed manifest, record each unique source receipt ID and one terminal decision: accepted, rejected for review, or unprocessed after failure. A count alone cannot reveal whether a source row was read twice after restart. The local [[spring/batch-skip-limit-check|skip test]] proves a three-row target and one skip, but it does not store this ledger."),
            ("Keep failure from masquerading as success",
            "If a failed job committed ID 1 before a later bad row exceeded the budget, the report must say partial. A rerun with the same manifest may revisit data. Key the reconciliation rows by manifest plus source ID, then compare content fingerprints before accepting another decision. [[spring/batch-job-identity|Job identity]] determines which execution history the operator is reviewing."),
            ("Limit sensitive retention",
            "Record a concise error code and source locator rather than copying an entire private row into logs. Set retention and access controls for correction queues. An audited correction is a new business decision, not a silent mutation of the original accepted row.")],
        code='record ImportDecision(String manifestId, String receiptId,\n    String state, String payloadHash, String reasonCode) {}',
        cost="A durable decision row adds one keyed write per source record and a review workflow. Hashes detect changed replay only when input normalization is stable.",
        mistakes=["Do not infer accepted count by subtracting skip count after a failed job.", "Do not log full private receipt payloads as a substitute for a correction queue.", "Do not mark skipped financial work completed without review."],
        related=["spring/batch-skip-limit-check", "spring/batch-retry-exhaustion", "spring/batch-job-identity", "spring/tenant-idempotency-key-scope"]),
    dict(slug="batch-durable-restart-check", section="spring/testing", family="batch", checked=False,
        title="Spring Batch crash recovery: test the repository and input across two processes",
        summary="An in-process restart proves less than a process-loss recovery because both metadata and input may disappear with the JVM.",
        blocks=[("Persist every recovery input",
            "The current kit's H2 database lives in one process. A crash check needs a durable JobRepository, a stable manifest, and source input that can be reopened at the same version. Launch process A, wait until a chunk commits, terminate it, then start process B with the same identifying parameters. Compare target IDs and versions, not only the job status."),
            ("Inject the hard window",
            "Kill the worker after the business write but before repository metadata is known to be durable. A correct design tolerates a repeated source ID through an explicit idempotency rule. [[spring/batch-idempotent-writer|The H2 writer test]] exposed a duplicate replay even without a process crash; a production database adds its own conflict and isolation behavior."),
            ("State what remains unproved",
            "A simulated exception in a single JVM is not this test. Neither the downloadable fixture nor this design sketch starts two processes or reconnects to a persistent database. Keep the claim limited until a two-process test runs that failure window.")],
        code='// Process A: launch manifest MANIFEST-47; terminate after a committed chunk.\n// Process B: relaunch MANIFEST-47 against the same durable repository.\n// Assert one target decision per source receipt ID.',
        cost="A process-kill test needs a durable database and orchestration, so it is slower than the in-memory contract tests. Run it at a separate integration tier.",
        mistakes=["Do not call an H2 in-process restart a crash-recovery proof.", "Do not change identifying parameters to make the second launch run.", "Do not rely on a cursor count for exactly-once output."],
        related=["spring/batch-job-identity", "spring/batch-idempotent-writer", "spring/batch-committed-chunk", "spring/testing-boundaries"]),
    dict(slug="modulith-sliced-context", section="spring/testing", family="modulith", checked=True,
        title="Spring Modulith module slices: start inventory without dispatch",
        summary="An ApplicationModuleTest starts managed beans for one module so wiring can be checked without booting its neighbors.",
        blocks=[("Inspect the context boundary",
            "The checked test is placed in the inventory package and uses ApplicationModuleTest. The context starts InventoryReservation; dispatchPlanner is absent. This proves the inventory bean can be constructed from its own module dependencies. The earlier [[spring/modulith-internal-violation|architecture check]] separately rejects a compiling import into an internal package."),
            ("Drive state and event together",
            "Reserving 19 units from a fixture balance of 47 leaves 28 and publishes one ReceiptReserved event for RECEIPT-203. An attempt to reserve 59 units for RECEIPT-211 leaves 47 and publishes no success event. [[spring/modulith-published-events|The event test]] inspects that boundary directly."),
            ("Keep the fixture claim local",
            "InventoryReservation stores balances in a concurrent map and publishes after the map update. The slice has no database transaction or publication registry. A crash between those two actions can lose the event. The test proves Spring wiring and in-process observation, not durable inventory accounting.")],
        code='@ApplicationModuleTest\nclass InventoryModuleIntegrationTest {\n    @Autowired InventoryReservation reservation;\n    @Autowired ApplicationContext context;\n}',
        cost="The slice starts Spring infrastructure and is slower than ApplicationModules.verify, but avoids starting unrelated module beans and remote adapters.",
        mistakes=["Do not call a package scan a running module context.", "Do not infer database atomicity from an in-memory map and event publisher.", "Do not mock away inventory when inventory is the module under test."],
        related=["spring/modulith-published-events", "spring/modulith-module-tests", "spring/modulith-module-api", "spring/transaction-events"]),
    dict(slug="modulith-published-events", section="spring/testing", family="modulith", checked=True,
        title="Spring Modulith PublishedEvents: assert an accepted fact and a rejected silence",
        summary="PublishedEvents records in-process events during a module test; it can assert both one accepted event and no event after rejection.",
        blocks=[("Match by business identity",
            "The source-kit test filters ReceiptReserved by receiptId. It sees one event for RECEIPT-203 after a valid reservation and none for RECEIPT-211 after a rejected 59-unit request. Checking a business key prevents an unrelated event of the same Java type from satisfying the assertion."),
            ("Observe the right thing",
            "PublishedEvents records application publication in the test context. It does not establish listener completion, a persisted registry entry or broker acceptance. For an asynchronous listener, a Scenario test needs an explicit deadline and a state or event expectation. [[spring/modulith-event-boundary|The event boundary]] names the later delivery steps."),
            ("Check the negative path",
            "The rejected command leaves the fixture balance unchanged and emits no successful fact. This is more useful than testing only the happy path: a false success event would let dispatch act on inventory that was never reserved.")],
        code='assertThat(events.ofType(ReceiptReserved.class)\n    .matching(ReceiptReserved::receiptId, "RECEIPT-203")).hasSize(1);',
        cost="Event assertions add little runtime cost beyond the Spring test context. A real publication registry writes one record per transactional listener and needs cleanup policy.",
        mistakes=["Do not interpret one published event as broker delivery.", "Do not assert only the event type when multiple receipts can publish it.", "Do not emit a success event for a rejected reservation."],
        related=["spring/modulith-sliced-context", "spring/modulith-event-boundary", "spring/modulith-registry-recovery", "spring/transaction-events"]),
    dict(slug="modulith-registry-recovery", section="spring/production", family="modulith", checked=False,
        title="Spring Modulith event registry recovery: separate publication, listener and broker states",
        summary="A configured publication registry can retain unfinished transactional-listener work, but it cannot itself prove downstream acceptance.",
        blocks=[("Persist the intended listener work",
            "With a supported registry starter and database schema, a transactional event publication can be recorded with the originating business transaction. A listener that fails leaves publication state available for a configured resubmission path. Test the same event identifier through failure, process restart and recovery. The current source kit does not install a registry starter or run this experiment."),
            ("Do not flatten the states",
            "An event may be published, in progress, failed, resubmitted or completed locally. A completed local listener can still hand a message to an external broker whose own acknowledgement and consumer processing are separate facts. [[spring/outbox-atomic-write|An outbox]] is another way to record external intent; neither design removes the need for consumer idempotency."),
            ("Bound replay and retention",
            "Set retry age, attempt budget and a terminal operator path. Keep completed publication records only as long as audit needs require. If a listener updates another store, use a stable event ID so resubmission does not apply the mutation twice.")],
        code='// Persist business change and publication intent in one transaction.\n// On restart, resubmit only eligible unfinished listener work.\n// Verify broker and consumer outcomes as separate contracts.',
        cost="Registry persistence adds a write per listener publication and maintenance for failed and completed rows. Recovery testing requires a durable database and process restart.",
        mistakes=["Do not equate a registry row with Kafka acceptance.", "Do not resubmit indefinitely without an operator path.", "Do not claim this design sketch is tested by the in-memory module slice."],
        related=["spring/modulith-published-events", "spring/modulith-event-boundary", "spring/outbox-atomic-write", "spring/consumer-dedup-transaction"]),
    dict(slug="modulith-event-ordering", section="spring/spring-core", family="modulith", checked=False,
        title="Spring Modulith event ordering: decide which state the listener may observe",
        summary="An in-process publication can occur before or after a transaction commits; listener timing must match the state contract.",
        blocks=[("Publish a fact after the guarded decision",
            "The inventory slice emits ReceiptReserved only after its in-memory reservation succeeds. In a database-backed command, publish while the business transaction is active so transactional listeners and a configured registry can associate the event with that decision. A regular synchronous listener may run before commit and must not assume other connections can read the new row."),
            ("Choose the observation point",
            "An after-commit listener can see committed state but its later failure cannot roll back that state change. For an external message, persist delivery intent with the business write and relay it separately. [[spring/transaction-events|Transaction-event timing]] and [[spring/outbox-atomic-write|outbox atomicity]] explain those two boundaries."),
            ("Keep per-key order explicit",
            "Two reservations for one receipt may publish events in a different order from listener completion when work is asynchronous. Carry receipt ID and version, then reject an older version at the consumer. The current module fixture has no asynchronous listener, database transaction or broker, so this remains a design contract.")],
        code='record ReceiptReserved(String receiptId, int units,\n                       int remaining, long version) {}',
        cost="Version checks add a keyed read or compare-and-set at the consumer. Asynchronous listeners add queues and backpressure decisions inside the process.",
        mistakes=["Do not assume an after-commit failure rolls back the source row.", "Do not infer listener completion order from event publication order.", "Do not call the local fixture a durable event system."],
        related=["spring/modulith-event-boundary", "spring/modulith-registry-recovery", "spring/transaction-events", "spring/consumer-dedup-transaction"]),
]

subjects = {"spring/production": "spring-production", "spring/testing": "spring-testing",
            "spring/spring-core": "spring-core"}
titles = {path: row["title"] for path, row in by.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
for index, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by, path
    assert all(target in titles for target in item["related"]), path
    body = paragraph(item["summary"])
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + paragraph(content)
    body += '<h2>' + ("Checked excerpt" if item["checked"] else "Boundary sketch") + '</h2><pre><code class="language-java">' + html.escape(item["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and verification</h2>" + paragraph(item["cost"] + (" The source kit checks the stated local behavior." if item["checked"] else " This design remains unexecuted in the source kit."))
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(m) + "</li>" for m in item["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(", ".join("[[" + target + "|" + titles[target] + "]]" for target in item["related"]) + ".")
    row = copy.deepcopy(by["spring/component-scan-vs-bean"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
        title=item["title"], summary=item["summary"], body=body, subject=subjects[item["section"]],
        tags=["spring", "spring-boot", "spring-" + item["family"], item["slug"]], sort_order=4300 + index,
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "framework_version": "Spring Boot 4.0.8; Batch 6.0.5 or Modulith 2.0.8 isolated kit",
        "java_version": "21 source-kit target",
        "verification_suite": ("BatchFaultPolicyContractTest" if item["family"] == "batch" else "InventoryModuleIntegrationTest") if item["checked"] else "Design sketch; integration test pending",
        "download_path": "/downloads/aitrove-spring-source-kit.zip",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    rows.append(row)
    by[path] = row

for section in subjects:
    for family, label in (("batch", "Batch fault handling"), ("modulith", "Modulith event and module tests")):
        paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section and item["family"] == family]
        if not paths:
            continue
        hub = by[section]
        hub["data"]["modules"].append({"title": label,
            "summary": "Read the checked local boundary and the next integration test.", "lessons": paths})
        hub["body"] += "<h2>" + label + "</h2><ul>" + "".join(
            '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths) + "</ul>"
        hub["updated_at"] = stamp

old = by["spring/batch-retry-skip-policy"]
old["body"] = old["body"].replace(
    "The downloadable Batch fixture does not configure retry or skip; this is a policy to test against the chosen exception classes.",
    "The downloadable Batch fixture now checks one accepted skip, a failed second skip, a transient recovery and exhausted retry. A real manifest still needs an explicit reconciliation record.")
old["body"] = old["body"].replace("This sketch is not executed by the source kit.",
    "The pseudocode is a policy outline; BatchFaultPolicyContractTest executes the stated skip and retry outcomes.")
old["body"] += "<h2>Checked fault-policy paths</h2>" + paragraph(
    "Inspect [[spring/batch-skip-limit-check|the skip-budget test]], [[spring/batch-retry-exhaustion|retry exhaustion]], and [[spring/batch-result-reconciliation|the remaining reporting design]].")
old["updated_at"] = stamp

old = by["spring/modulith-event-boundary"]
old["body"] = old["body"].replace(
    "The current isolated Modulith project tests package structure only, so the event flow here is a design sketch awaiting a registry and restart test.",
    "The isolated module slice now checks in-process publication for an accepted reservation and silence for a rejected one. Registry persistence and restart remain untested.")
old["body"] += "<h2>Checked publication and remaining delivery</h2>" + paragraph(
    "See [[spring/modulith-published-events|the in-process event test]], then [[spring/modulith-registry-recovery|the untested registry recovery boundary]].")
old["updated_at"] = stamp

old = by["spring/modulith-module-tests"]
old["body"] = old["body"].replace(
    "The downloaded Modulith project has two fast classpath checks: one accepted root API dependency and one rejected internal import. They never start Spring. When inventory has managed beans, add an ApplicationModuleTest in the inventory package, drive a reservation, assert its published event and check database state. A sliced context exposes hidden bean dependencies that a package scan cannot instantiate.",
    "The downloaded Modulith project now has two classpath checks and two ApplicationModuleTest checks. The inventory slice starts Spring, constructs InventoryReservation without dispatchPlanner, then checks an accepted reservation event and a rejected command with no success event. Its state is an in-memory map; database atomicity remains untested.")
old["body"] = old["body"].replace("// Add @ApplicationModuleTest when inventory has managed beans.",
    "// InventoryModuleIntegrationTest also starts a sliced context.")
old["body"] = old["body"].replace("This sketch is not executed by the source kit.",
    "InventoryModuleIntegrationTest checks the sliced context; registry delivery remains untested.")
old["body"] += "<h2>Running module slice</h2>" + paragraph(
    "Open [[spring/modulith-sliced-context|the context boundary]] and [[spring/modulith-published-events|the event assertion]].")
old["data"]["verification_suite"] = "ModulithBoundaryContractTest and InventoryModuleIntegrationTest"
old["updated_at"] = stamp

for source, target in (("spring/batch-job-identity", "spring/batch-durable-restart-check"),
                       ("spring/batch-idempotent-writer", "spring/batch-result-reconciliation"),
                       ("spring/modulith-module-api", "spring/modulith-sliced-context"),
                       ("spring/transaction-events", "spring/modulith-event-ordering"),
                       ("spring/testing-boundaries", "spring/batch-durable-restart-check")):
    row = by[source]
    row["body"] += "<h2>Related Spring path</h2>" + paragraph(
        "Continue with [[" + target + "|" + titles[target] + "]].")
    row["updated_at"] = stamp

root = by["spring/spring-boot"]
root["body"] += "<h2>Batch faults and module events</h2>" + paragraph(
    "Check [[spring/batch-skip-limit-check|the Batch skip budget]] and [[spring/modulith-sliced-context|the running inventory module slice]].")
root["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring Batch and Modulith lessons")

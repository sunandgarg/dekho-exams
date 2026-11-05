"""Publish Batch and Modulith lessons tied to isolated checked source projects."""

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
    dict(slug="batch-job-identity", section="spring/production", family="batch", checked=True,
        title="Spring Batch job identity: a manifest ID defines restart versus a new run",
        summary="A JobInstance is identified by its job name and identifying parameters; completing one instance blocks an identical rerun.",
        blocks=[("Keep the manifest stable across recovery",
            "The checked job runs with identifying manifestId MANIFEST-47. Its first execution fails, then a second launch with the same parameter restarts that instance. A different manifest ID creates another instance. Do not add the current time merely to evade a failed job: that creates new work and can duplicate rows already committed. [[spring/batch-idempotent-writer|The writer]] must still make repeated source IDs safe."),
            ("Treat completion as a recorded outcome",
            "A separate run with MANIFEST-93 completes four rows. Launching MANIFEST-93 again raises JobInstanceAlreadyCompleteException and leaves the target count at four. That assertion uses one H2 process. Recovery after a process crash needs a durable JobRepository and stable access to the original input. [[spring/batch-committed-chunk|The chunk lesson]] locates the earlier commit.")],
        code='JobParameters run = new JobParametersBuilder()\n    .addString("manifestId", "MANIFEST-47")\n    .toJobParameters();\nJobExecution first = launcher.run(receiptImportJob, run);',
        cost="Each execution reads and writes repository metadata. A business manifest key also needs retention and a correction policy for input that has already completed.",
        mistakes=["Do not use a random parameter when the intention is to restart the same work.", "Do not equate job completion with proof that every external side effect arrived.", "Do not rely on an in-memory H2 repository for recovery across process loss."],
        related=["spring/batch-committed-chunk", "spring/batch-idempotent-writer", "spring/batch-chunk-restart", "spring/testing-boundaries"]),
    dict(slug="batch-committed-chunk", section="spring/data-transactions", family="batch", checked=True,
        title="Spring Batch chunks: a later failure does not erase an earlier commit",
        summary="A chunk step commits each successful group under its transaction manager; a later failing group rolls back its own writes.",
        blocks=[("Observe the cut point",
            "The source kit reads four receipt rows and writes two at a time. IDs 1 and 2 commit. The writer then throws after attempting ID 3 in the next group; the job is FAILED, the target table still has two rows, and ID 3 did not persist. A job-wide all-or-nothing import needs a different design. [[spring/transaction-propagation|Transaction propagation]] does not merge distinct chunk commits."),
            ("Choose size for the resource",
            "A larger chunk lowers commit frequency but retains more rows and holds locks longer. A smaller chunk spends more time committing and updating metadata. Measure with actual row size and database contention. The H2 check says nothing about an HTTP call or broker send made inside a writer: that remote side effect will not roll back with this database chunk.")],
        code='return new StepBuilder("receiptImportStep", repository)\n    .<ReceiptRow, ReceiptRow>chunk(2)\n    .transactionManager(transactionManager)\n    .reader(receiptReader).writer(receiptWriter).build();',
        cost="For n rows and chunk size c, expect roughly ceil(n/c) chunk commits plus repository work. Memory grows with c and the transformed item size.",
        mistakes=["Do not claim one job-wide rollback from a chunk step.", "Do not assume a remote side effect rolls back with the chunk.", "Do not choose a large chunk without measuring lock time."],
        related=["spring/batch-job-identity", "spring/batch-idempotent-writer", "spring/outbox-atomic-write", "spring/batch-chunk-restart"]),
    dict(slug="batch-idempotent-writer", section="spring/data-transactions", family="batch", checked=True,
        title="Spring Batch writers: use a stable source key when a chunk is replayed",
        summary="A restart can encounter a previously committed item; a stable business key lets the destination detect or reconcile that replay.",
        blocks=[("Make the replay decision visible",
            "The H2 fixture keys receipt_import by source ID. A plain INSERT exposed a duplicate-key failure on restart even though the first chunk had committed. The checked writer uses H2 MERGE keyed by ID. After restart, the table has four rows: ID 1 retains seven units and ID 4 has 28. This MERGE syntax is H2-specific. A production ledger should also reject a reused source ID whose payload changed, rather than silently overwriting it."),
            ("Keep writer state separate from metadata",
            "The failed execution's saved reader context reports two reads, yet the local restart can revisit earlier rows. Even with another reader implementation, a crash between business and repository commits can make replay possible. Keep the sink key stable and the operation idempotent. An external broker send is a separate side effect; [[spring/outbox-atomic-write|the outbox]] records intent inside the business transaction.")],
        code='jdbc.update("MERGE INTO receipt_import (id, units) KEY (id) VALUES (?, ?)",\n    receipt.id(), receipt.units());',
        cost="The unique key adds indexed lookup work per row. An upsert may write an existing row again; compare content or version before accepting a changed replay.",
        mistakes=["Do not silently overwrite a changed source record under the same ID.", "Do not confuse a saved reader count with exactly-once output.", "Do not copy H2 MERGE syntax into another database without checking semantics."],
        related=["spring/batch-committed-chunk", "spring/batch-job-identity", "spring/outbox-atomic-write", "spring/tenant-idempotency-key-scope"]),
    dict(slug="batch-retry-skip-policy", section="spring/production", family="batch", checked=False,
        title="Spring Batch skip and retry policy: distinguish bad input from temporary failure",
        summary="A retry repeats an item; a skip removes it from successful output, so both choices need explicit business rules.",
        blocks=[("Classify the failure",
            "Malformed UTF-8 in a manifest is deterministic for those bytes; repetition will not repair it. A brief database deadlock may justify a bounded retry. A missing tenant mapping should stop the job until corrected, not vanish into a skip count. Record the rejected source ID without logging private row text. [[spring/multipart-receipt-import|Upload validation]] can reject several inputs before the job starts."),
            ("Bound the tail",
            "Set retry and skip limits, then fail the job when a threshold is crossed. A COMPLETED job with unexamined skipped financial rows is a misleading outcome. Produce a reconciliation record with accepted, rejected and retried counts. The downloadable Batch fixture does not configure retry or skip; this is a policy to test against the chosen exception classes.")],
        code='if (malformedReceiptId) rejectManifest();\nif (transientDatabaseConflict) retryWithinBound();\nif (unknownTenant) stopForOperatorReview();',
        cost="Each retry can repeat a chunk's reads and writes. Skips reduce successful output and create reconciliation work; keep both counters bounded.",
        mistakes=["Do not retry a deterministic parse error.", "Do not skip a row that changes a financial total without reconciliation.", "Do not claim the local Batch tests verify this policy."],
        related=["spring/batch-idempotent-writer", "spring/multipart-receipt-import", "spring/schema-backfill-batch", "spring/batch-job-identity"]),
    dict(slug="modulith-module-api", section="spring/spring-core", family="modulith", checked=True,
        title="Spring Modulith module APIs: call the inventory root package, not its internals",
        summary="A module's root package is its default API boundary; another module should not import classes from its internal packages.",
        blocks=[("Arrange by capability",
            "The isolated source project places InventoryQueries in the inventory root package and StockStore in inventory.internal. DispatchPlanner imports InventoryQueries. ApplicationModules.verify accepts that graph. The main application's direct child packages become the two modules in this simple arrangement. [[spring/constructor-injection|Constructor injection]] keeps the dependency visible."),
            ("Make the forbidden import fail",
            "A second fixture imports a public class from inventory.internal. Java compiles it, but Modulith verification rejects it. That test catches coupling that would make an internal refactor break dispatch. A module API is not a network boundary or a permission check. The same process still needs transaction and tenant rules for data mutations.")],
        code='ApplicationModules.of(ReceiptModulesApplication.class).verify();',
        cost="Verification scans compiled classes during tests. A valid module call remains a local method call and adds no network hop.",
        mistakes=["Do not expose an internal type merely to satisfy another module's import.", "Do not equate a package rule with tenant authorization.", "Do not make every class part of the module API."],
        related=["spring/modulith-internal-violation", "spring/modulith-module-tests", "spring/constructor-injection", "spring/tenant-receipt-authorization"]),
    dict(slug="modulith-internal-violation", section="spring/testing", family="modulith", checked=True,
        title="Spring Modulith verification: a compiling internal import still fails architecture checks",
        summary="The Java compiler accepts a public internal class, but ApplicationModules.verify can reject cross-module access to it.",
        blocks=[("Test both sides",
            "The source kit runs two architecture checks. Its valid dispatch module references the inventory root API and passes. Its invalid dispatch module constructs inventory.internal.UnsafeStockStore; verification throws despite both fixtures compiling. These tests demonstrate the package rule. They do not start the Spring context or execute a listener. [[spring/modulith-module-api|The API lesson]] shows the accepted dependency."),
            ("Run on the real root",
            "The accepted and rejected package trees are separate roots so one intentional violation does not poison the valid fixture. In a product, verify the actual application root in CI. Do not disable the rule globally because a public internal type seems convenient; move required behavior into an explicit root API or named interface.")],
        code='assertDoesNotThrow(() -> ApplicationModules.of(\n    ReceiptModulesApplication.class).verify());\nassertThrows(RuntimeException.class, () -> ApplicationModules.of(\n    InvalidReceiptModulesApplication.class).verify());',
        cost="Architecture scans consume build time, not request time. They catch coupling before broad integration tests become difficult to isolate.",
        mistakes=["Do not assume public means intended as a module API.", "Do not verify only a tiny fixture when the production graph is the subject.", "Do not claim these checks cover event delivery."],
        related=["spring/modulith-module-api", "spring/modulith-module-tests", "spring/testing-boundaries", "spring/spring-core"]),
    dict(slug="modulith-event-boundary", section="spring/spring-core", family="modulith", checked=False,
        title="Spring Modulith events: publish a domain fact after a valid state change",
        summary="An in-process event can loosen module coupling, but publication alone does not guarantee durable external delivery.",
        blocks=[("Name a committed fact",
            "Inventory can publish ReceiptReserved after recording a successful reservation. Dispatch listens for that fact instead of reading inventory.internal. A failed version check must emit no successful event. [[spring/transaction-events|Transaction event timing]] determines when a listener sees committed state; [[spring/outbox-atomic-write|the outbox]] records an external delivery intent with the state change."),
            ("Account for listener failure",
            "A synchronous listener can fail the publisher; an asynchronous one can fail after the caller returns. Spring Modulith's publication registry can persist outstanding transactional-listener publications when installed and configured. That is not identical to Kafka acceptance. The current isolated Modulith project tests package structure only, so the event flow here is a design sketch awaiting a registry and restart test.")],
        code='record ReceiptReserved(String tenantId, String receiptId,\n                       int units, long version) {}\n// Publish only after the guarded reservation decision succeeds.',
        cost="Events reduce direct package coupling but add ordering, duplicate and recovery decisions. A persisted registry adds database writes per publication.",
        mistakes=["Do not publish a successful domain event before a valid state change.", "Do not call an in-process event a durable queue.", "Do not assume a broker send rolls back with the database."],
        related=["spring/modulith-module-api", "spring/modulith-module-tests", "spring/transaction-events", "spring/outbox-atomic-write"]),
    dict(slug="modulith-module-tests", section="spring/testing", family="modulith", checked=False,
        title="Spring Modulith module tests: distinguish structure verification from a sliced context",
        summary="ApplicationModules.verify inspects dependencies; a module-sliced Spring context checks bean wiring and behavior.",
        blocks=[("Use the cheapest proof first",
            "The downloaded Modulith project has two fast classpath checks: one accepted root API dependency and one rejected internal import. They never start Spring. When inventory has managed beans, add an ApplicationModuleTest in the inventory package, drive a reservation, assert its published event and check database state. A sliced context exposes hidden bean dependencies that a package scan cannot instantiate."),
            ("Keep external work in a separate test",
            "A module test may replace a neighboring module API with a controlled collaborator, but the real cross-module contract still needs a combined test. For asynchronous listeners, use an explicit await condition and deadline. Do not make a test pass by sleeping an arbitrary amount or by declaring a publication successful before its transaction commits. [[spring/testing-boundaries|The broader test guide]] places those layers.")],
        code='ApplicationModules.of(ReceiptModulesApplication.class).verify();\n// Add @ApplicationModuleTest when inventory has managed beans.',
        cost="A classpath scan is cheap. A module-sliced context starts Spring infrastructure; a full application test is slower but checks the assembled graph.",
        mistakes=["Do not call a package-only check a running integration test.", "Do not mock away the boundary under test.", "Do not infer broker delivery from a published in-process event."],
        related=["spring/modulith-internal-violation", "spring/modulith-event-boundary", "spring/testing-boundaries", "spring/tenant-command-api-project"]),
]

subjects = {"spring/production": "spring-production", "spring/data-transactions": "spring-data",
            "spring/testing": "spring-testing", "spring/spring-core": "spring-core"}
titles = {path: row["title"] for path, row in by.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
for index, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by, path
    assert all(target in titles for target in item["related"]), (path, [target for target in item["related"] if target not in titles])
    body = paragraph(item["summary"])
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + paragraph(content)
    body += '<h2>' + ("Checked excerpt" if item["checked"] else "Boundary sketch") + '</h2><pre><code class="language-java">' + html.escape(item["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and verification</h2>" + paragraph(item["cost"] + (" The isolated source-kit project checks the stated local behavior." if item["checked"] else " This sketch is not executed by the source kit."))
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(m) + "</li>" for m in item["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(", ".join("[[" + target + "|" + titles[target] + "]]" for target in item["related"]) + ".")
    row = copy.deepcopy(by["spring/component-scan-vs-bean"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
        title=item["title"], summary=item["summary"], body=body, subject=subjects[item["section"]],
        tags=["spring", "spring-boot", "spring-" + item["family"], item["slug"]], sort_order=4200 + index,
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4.0.8; Batch 6.0.5 or Modulith 2.0.8 isolated kit",
        "java_version": "21 source-kit target",
        "verification_suite": ("BatchBoundaryContractTest" if item["family"] == "batch" else "ModulithBoundaryContractTest") if item["checked"] else "Design sketch; integration test pending",
        "download_path": "/downloads/aitrove-spring-source-kit.zip",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    rows.append(row)
    by[path] = row

for section in subjects:
    for family, label in (("batch", "Batch restart and recovery"), ("modulith", "Modulith module and event boundaries")):
        paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section and item["family"] == family]
        if not paths:
            continue
        hub = by[section]
        hub["data"]["modules"].append({"title": label, "summary": "Inspect the local proof and the remaining deployment boundary.", "lessons": paths})
        hub["body"] += "<h2>" + label + "</h2><ul>" + "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths) + "</ul>"
        hub["updated_at"] = stamp

old = by["spring/batch-chunk-restart"]
old["body"] = old["body"].replace(
    "Restart must resume according to the reader and JobRepository state, not simply begin from line one and hope duplicates are harmless.",
    "A restart uses reader and JobRepository state, but the destination still needs a stable source key: the checked four-row fixture revisited committed rows, and a plain INSERT failed on their IDs.")
old["body"] += "<h2>Checked local restart</h2>" + paragraph(
    "The downloadable [[spring/batch-committed-chunk|chunk test]] leaves two rows committed after a later failure. "
    "Its saved reader count is two, while [[spring/batch-idempotent-writer|an H2 key-based writer]] lets the same instance finish on restart. "
    "This is an in-process H2 check, not a process-crash recovery test.")
old["updated_at"] = stamp
root = by["spring/spring-boot"]
root["body"] += "<h2>Batch and module architecture</h2>" + paragraph(
    "Read [[spring/batch-job-identity|job identity]] before running a restartable import, then inspect "
    "[[spring/batch-committed-chunk|chunk commits]] and [[spring/modulith-module-api|module APIs]].")
root["updated_at"] = stamp
for source, target in (("spring/schema-backfill-batch", "spring/batch-idempotent-writer"),
                       ("spring/transaction-events", "spring/modulith-event-boundary"),
                       ("spring/testing-boundaries", "spring/modulith-module-tests"),
                       ("spring/outbox-atomic-write", "spring/modulith-event-boundary")):
    row = by[source]
    row["body"] += "<h2>Related Spring path</h2>" + paragraph("Continue with [[" + target + "|" + titles[target] + "]].")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Batch and Modulith lessons")

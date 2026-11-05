"""Add original Spring Batch recovery lessons and correct older proof boundaries."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

root = pathlib.Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def linked(text):
    return re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]", lambda match:
        '<a href="/' + match[1] + '">' + html.escape(match[2]) + "</a>", html.escape(text))


lessons = [
    dict(slug="batch-two-process-recorded-restart", section="spring/production", checked=True,
        title="Spring Batch restart across two JVMs after a recorded failed execution",
        summary="A file-backed JobRepository retains a failed execution and its committed business rows after the first JVM exits.",
        blocks=[
            ("Hold the job identity still", "The source kit launches MANIFEST-263 twice against the same file-backed H2 database. Process A writes IDs 1 and 2, then fails while writing the next chunk. It exits after Spring records FAILED. Process B starts a fresh JVM with the same manifest parameter. It sees the same JobInstance ID, completes the job, and leaves exactly IDs 1, 2, 3 and 4 in the target. [[spring/batch-job-identity|The identifying parameter]] is the join between those executions."),
            ("Observe rows, not just status", "The test checks both the Batch status and the target IDs after each process. A COMPLETED label alone could hide a missing record. The writer uses an H2 key-based MERGE, so a replay cannot create a duplicate source ID; it could still overwrite a changed payload. [[spring/batch-input-snapshot|Input versioning]] and a payload comparison are separate requirements."),
            ("Mark the fault boundary", "This is a graceful process exit after a recorded failure. It is not a kill during a database commit. The child JVM is gone before the second launch, so repository durability is checked, but [[spring/batch-running-execution-recovery|an orphaned STARTED execution]] and the business-write/metadata-commit race are not. Test those against the intended database before advertising abrupt-crash recovery.")],
        code='String databaseUrl = "jdbc:h2:file:" + temporaryDirectory.resolve("durable-receipts");\nString failed = launch(databaseUrl, "fail", "MANIFEST-263");\nString resumed = launch(databaseUrl, "resume", "MANIFEST-263");\nassertEquals(instance(failed), instance(resumed));',
        cost="Two Boot startups and disk-backed metadata make this slower than an in-memory step test. H2 file semantics cannot establish the same commit window as a production database.",
        mistakes=["Do not call an orderly FAILED execution an abrupt process crash.", "Do not change the identifying manifest ID for the second launch.", "Do not infer exactly-once business effects from a final row count alone."],
        related=["spring/batch-durable-restart-check", "spring/batch-job-identity", "spring/batch-input-snapshot", "spring/batch-running-execution-recovery"]),
    dict(slug="batch-running-execution-recovery", section="spring/production", checked=False,
        title="Spring Batch orphaned STARTED execution: inspect before relaunch",
        summary="A process killed without recording failure can leave repository metadata in a running state even when no worker is alive.",
        blocks=[
            ("Do not invent another instance", "A scheduler sees no live worker, but the JobRepository may still show STARTED because the process died before recording an ending status. Relaunching with the same identifying parameters can be refused as already running. Adding a timestamp creates new work, bypasses the old execution history and risks repeated writes. [[spring/batch-two-process-recorded-restart|The checked two-JVM test]] deliberately starts from FAILED, not this state."),
            ("Fence recovery", "First prove that the old worker cannot still write: check process ownership, scheduler lease and target database connections. Inspect the repository's JobExecution and StepExecution records, the last committed business key and source version. Only then apply the recovery procedure appropriate to the installed Batch version and repository store. Record the operator action and resume with the original manifest. There is no safe universal SQL update for every installation."),
            ("Test the real failure window", "A controlled integration test can stop the worker after a committed chunk, restart the application, and assert that recovery does not run alongside the old process. A second test should stop it between a business write and metadata update. Compare durable decisions by source ID. The source kit does not force-kill a process, so this remains a design boundary.")],
        code='// Inspect the persisted execution and confirm the old worker is fenced.\n// Apply the installed repository recovery procedure, then restart\n// with the original identifying manifestId.',
        cost="Recovery needs an operator or controller with repository access and a fencing signal. A false death decision can run two workers on the same manifest.",
        mistakes=["Do not turn an orphaned execution into a new manifest silently.", "Do not edit Batch metadata while the original worker may still be alive.", "Do not claim a two-JVM graceful failure test covers kill -9."],
        related=["spring/batch-two-process-recorded-restart", "spring/batch-durable-restart-check", "spring/batch-idempotent-writer", "spring/batch-input-snapshot"]),
    dict(slug="batch-input-snapshot", section="spring/data-transactions", checked=False,
        title="Spring Batch restart input: pin the manifest before resuming a cursor",
        summary="A durable repository cannot reconstruct the same import if the source rows change between executions.",
        blocks=[
            ("Freeze the source set", "The checked two-process fixture keeps four database rows unchanged. A real import may read a CSV replaced at the same path or a query whose result changes while the job is down. Persist a manifest that names an immutable object version or source snapshot, includes a count and digest, and becomes part of the job's business identity. A location string by itself is not a version."),
            ("Reject changed replay", "Before resuming, recompute the manifest digest or reopen the immutable object version. If it differs, fail for review. Do not let [[spring/batch-idempotent-writer|an upsert writer]] conceal a changed receipt under the same source ID. For mutable database sources, use a snapshot or a bounded query over versioned rows; a new row inserted ahead of the cursor can shift ordering if the reader relies on position."),
            ("Separate correction from restart", "A corrected source file is a new business input. Give it a new manifest identity and record its relationship to the earlier failed one. Reusing the old identity with new bytes makes the saved checkpoint meaningless. The current kit does not mutate source rows between launches; this policy still needs an integration test.")],
        code='record ImportManifest(String manifestId, String sourceVersion,\n                      long sourceCount, String sha256) {}\n// Reopen the pinned sourceVersion and compare its digest before restart.',
        cost="Immutable input consumes storage and retention time. Digesting a large source is linear in its byte size and may require a separate pass.",
        mistakes=["Do not treat a pathname as immutable input.", "Do not resume a positional cursor over a reordered query result.", "Do not overwrite a changed receipt because its ID already exists."],
        related=["spring/batch-two-process-recorded-restart", "spring/batch-idempotent-writer", "spring/batch-job-identity", "spring/batch-result-reconciliation"]),
    dict(slug="batch-skip-quarantine", section="spring/data-transactions", checked=True,
        title="Spring Batch SkipListener: persist a rejection key with the skipped row",
        summary="A skipped item needs a durable, keyed reason record if the business must review it after a completed job.",
        blocks=[
            ("Put a decision beside the count", "The checked fault-policy fixture skips source ID 2 for negative units. Its SkipListener writes ID 2 and reason INVALID_UNITS into policy_rejection. Three valid IDs reach policy_target. The test also checks that exhausted retry produces no rejection. A retryable infrastructure fault is not a bad business row. [[spring/batch-retry-skip-policy|The policy lesson]] sets the exception classes and limits."),
            ("Key callbacks for replay", "The H2 quarantine table uses the source ID as primary key and MERGE for repeated callbacks. Batch may invoke a skip callback again after rollback, so a listener must not append duplicate decisions blindly. In a multi-manifest service, include the manifest ID in the key; the fixture has one isolated job at a time and does not prove cross-manifest isolation."),
            ("Keep the transaction claim local", "This listener writes through the same JdbcTemplate in the local step and its assertion observes the resulting row. A remote review queue or second database has another transaction boundary. Do not infer that it commits atomically with the chunk without a check using the actual resources. [[spring/batch-result-reconciliation|Full reconciliation]] still needs source count and operator disposition.")],
        code='@Override\npublic void onSkipInProcess(PolicyRow receipt, Throwable failure) {\n    jdbc.update("MERGE INTO policy_rejection (id, reason_code) " +\n        "KEY(id) VALUES (?, ?)", receipt.id(), "INVALID_UNITS");\n}',
        cost="Each rejected row adds a keyed database write. The H2 MERGE syntax and lock behavior must be adapted and measured on the target database.",
        mistakes=["Do not use a plain append-only insert if the callback may repeat.", "Do not place full private payloads in a general log as the review record.", "Do not label an exhausted transient retry as rejected input."],
        related=["spring/batch-skip-limit-check", "spring/batch-retry-skip-policy", "spring/batch-result-reconciliation", "spring/batch-two-process-recorded-restart"]),
    dict(slug="batch-restart-verification-matrix", section="spring/testing", checked=False,
        title="Spring Batch restart test matrix: separate failure, process loss and changed input",
        summary="One green restart test covers only its own failure window and resource combination.",
        blocks=[
            ("Start with the checked case", "The source kit now has an in-process chunk restart and a separate two-JVM run after FAILED was recorded. It also checks one skipped row, a second row exceeding the skip budget and an exhausted temporary retry. Those are distinct behaviors. Keep their assertions on target IDs, rejected IDs and JobInstance identity, rather than relying on a log line that says COMPLETED."),
            ("Add the unproved windows", "A target-database suite should kill a process after one commit, during a business write and after that write but before repository progress is durable. Another suite should replace or reorder source input between attempts and prove that the manifest guard rejects it. Run two competing launchers to verify fencing. None of these cases is covered by file-backed H2 after an orderly FAILED state."),
            ("Review outcome, not only framework state", "A completed job with one skipped item still has a business exception. The report should name accepted, rejected and unprocessed IDs per manifest. [[spring/batch-skip-quarantine|The local quarantine check]] stores one rejected key; it does not implement a complete audited correction workflow.")],
        code='// Assert after each boundary: JobInstance ID, BatchStatus,\n// accepted source IDs, rejected source IDs and input version.',
        cost="Fault injection requires process orchestration and a real repository. Keep fast unit checks separate from the slower destructive integration suite.",
        mistakes=["Do not substitute an exception in one JVM for a process kill.", "Do not use only row counts when IDs can be duplicated or omitted.", "Do not call a skipped financial row a fully accepted import."],
        related=["spring/batch-two-process-recorded-restart", "spring/batch-running-execution-recovery", "spring/batch-input-snapshot", "spring/batch-skip-quarantine"]),
]

all_titles = {path: row["title"] for path, row in by_path.items()}
all_titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subject_ids = {"spring/production": "spring-production", "spring/data-transactions": "spring-data", "spring/testing": "spring-testing"}
for index, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    assert all(target in all_titles for target in item["related"])
    body = "<p>" + linked(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + linked(content) + "</p>"
    body += "<h2>" + ("Checked excerpt" if item["checked"] else "Boundary sketch") + '</h2><pre><code class="language-java">' + html.escape(item["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and verification</h2><p>" + html.escape(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2><p>" + ", ".join('<a href="/' + target + '">' + html.escape(all_titles[target]) + "</a>" for target in item["related"]) + ".</p>"
    row = copy.deepcopy(by_path["spring/component-scan-vs-bean"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
        title=item["title"], summary=item["summary"], body=body, subject=subject_ids[item["section"]],
        tags=["spring", "spring-boot", "spring-batch", item["slug"]], sort_order=4300 + index,
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "framework_version": "Spring Boot 4.0.8; Spring Batch 6.0.5 source-kit target",
        "java_version": "21 source-kit target",
        "verification_suite": ("TwoProcessRestartContractTest" if item["slug"] == "batch-two-process-recorded-restart" else "BatchFaultPolicyContractTest") if item["checked"] else "Design boundary; target-database check pending",
        "download_path": "/downloads/aitrove-spring-source-kit.zip",
        "related": [{"path": target, "title": all_titles[target]} for target in item["related"]]}
    rows.append(row)
    by_path[path] = row

for section in subject_ids:
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    if not paths:
        continue
    hub = by_path[section]
    hub["data"]["modules"].append({"title": "Batch recovery and rejected-row review",
        "summary": "Run the checked local boundaries, then identify the production failure windows still open.",
        "lessons": paths})
    hub["body"] += "<h2>Batch recovery and rejected-row review</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(all_titles[path]) + "</a></li>" for path in paths) + "</ul>"
    hub["updated_at"] = stamp

durable = by_path["spring/batch-durable-restart-check"]
durable["title"] = "Spring Batch restart boundaries: recorded failure versus abrupt process loss"
durable["summary"] = "A two-process test now proves restart after a recorded FAILED execution; abrupt-kill recovery remains a separate boundary."
durable["body"] = (
    "<p>A file-backed JobRepository preserves job history across JVM exit. The source kit now proves restart after a recorded failed execution, while an abrupt process kill remains untested.</p>"
    "<h2>Use the checked path first</h2><p>Process A commits receipt IDs 1 and 2, records FAILED and exits. Process B starts against the same H2 file with the same identifying manifest ID. It observes the same JobInstance and completes with IDs 1 through 4. <a href=\"/spring/batch-two-process-recorded-restart\">The two-JVM lesson</a> states the exact assertions. This is a meaningful durability check; the first process had already recorded its failure.</p>"
    "<h2>Keep abrupt death separate</h2><p>A process killed before repository status is updated may leave STARTED metadata. Relaunch can be refused until the old worker is fenced and the execution is reconciled. A kill between business and repository writes may replay input. <a href=\"/spring/batch-running-execution-recovery\">The running-state guide</a> maps that operational boundary, while <a href=\"/spring/batch-input-snapshot\">the input guide</a> pins the bytes being resumed. Neither is established by the checked two-JVM case.</p>"
    '<h2>Checked excerpt</h2><pre><code class="language-java">String first = launch(databaseUrl, "fail", "MANIFEST-263");\nString second = launch(databaseUrl, "resume", "MANIFEST-263");\nassertEquals(instance(first), instance(second));</code></pre>'
    "<h2>Cost and verification</h2><p>The checked test starts Spring Boot twice and uses file-backed H2. Target-database locking, a hard kill and source replacement remain unproved.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not call a recorded FAILED state an abrupt crash.</li><li>Do not create a new manifest merely to bypass an orphaned running execution.</li><li>Do not infer identical source input from a stable filename.</li></ul>"
    "<h2>Read next</h2><p><a href=\"/spring/batch-two-process-recorded-restart\">Two-process recorded restart</a>, <a href=\"/spring/batch-running-execution-recovery\">running-execution recovery</a>, <a href=\"/spring/batch-restart-verification-matrix\">restart test matrix</a>.</p>"
)
durable["data"]["verification_suite"] = "TwoProcessRestartContractTest; abrupt-kill path pending"
durable["updated_at"] = stamp

skip = by_path["spring/batch-skip-limit-check"]
skip["body"] = skip["body"].replace(
    "The source kit checks counts but does not persist a quarantine table or an operator approval workflow.",
    "The source kit now persists ID 2 with a reason code in an H2 quarantine table; an operator approval workflow remains unimplemented. See <a href=\"/spring/batch-skip-quarantine\">the checked listener</a>.")
skip["updated_at"] = stamp

policy = by_path["spring/batch-retry-skip-policy"]
policy["body"] = policy["body"].replace(
    "A real manifest still needs an explicit reconciliation record.",
    "The local SkipListener stores one rejected source key; a real manifest still needs full reconciliation and review.")
policy["body"] = policy["body"].replace(
    "Do not claim the local Batch tests verify this policy.",
    "Do not claim the local Batch tests classify every production database error.")
policy["updated_at"] = stamp

reconciliation = by_path["spring/batch-result-reconciliation"]
reconciliation["body"] = reconciliation["body"].replace(
    "but it does not store this ledger.",
    "and the <a href=\"/spring/batch-skip-quarantine\">listener test</a> stores one rejected ID and reason. Neither stores the full per-manifest decision ledger.")
reconciliation["updated_at"] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring Batch lessons; total Spring articles:",
    sum(row["path"].startswith("spring/") and row.get("type") == "article" for row in rows))

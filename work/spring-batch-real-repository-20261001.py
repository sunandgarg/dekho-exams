"""Publish verified Batch JDBC, abrupt-death and source-integrity boundaries."""

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


def paragraph(value):
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]", lambda match:
        '<a href="/' + match[1] + '">' + match[2] + "</a>", escaped) + "</p>"


lessons = [
    dict(slug="batch-jdbc-repository-boot4", section="spring/production", checked=True,
        title="Spring Boot 4 Batch JDBC starter: verify that job history is actually stored",
        summary="Business rows on disk do not prove Batch metadata is durable; the JobRepository needs its own JDBC configuration.",
        blocks=[
            ("Inspect the repository, not its surroundings", "A file-backed DataSource can coexist with an in-memory Batch repository. Both JVMs might print JobInstance ID 1 simply because each started a fresh repository. That is not restart. The source kit now uses the Boot 4 JDBC Batch starter and checks the BATCH_JOB_INSTANCE and BATCH_JOB_EXECUTION tables after two runs: one instance, two executions. [[spring/batch-two-process-recorded-restart|The recorded-failure test]] checks the same persisted identity across process boundaries."),
            ("Keep the schema on the same database", "The first test launch initializes Batch metadata in the H2 file; the second launch does not recreate that schema. Business rows and Batch metadata use the same local DataSource. This is a fixture choice. A deployed service may use a separate repository database, but the job must connect to the same durable repository on every attempt. Check the actual configured JobRepository bean and schema before relying on restart."),
            ("Guard the production claim", "A resourceless repository is valid for jobs that do not need restart history. It is wrong for a job advertised as resumable. A row count of four after two processes proves neither persistence nor a single JobInstance when the writer uses an upsert. Inspect metadata directly and try an abrupt-death case as [[spring/batch-killed-worker-recovery|the checked recovery test]] does.")],
        code='<dependency>\n  <groupId>org.springframework.boot</groupId>\n  <artifactId>spring-boot-starter-batch-jdbc</artifactId>\n</dependency>',
        language="xml", cost="JDBC job metadata adds writes around launches, steps and commits. Retain and back up its tables under a policy tied to audit and restart needs.",
        mistakes=["Do not infer a JDBC JobRepository from the presence of JdbcTemplate.", "Do not treat matching auto-generated IDs in separate empty repositories as proof of a restart.", "Do not initialize Batch metadata anew on every retry."],
        related=["spring/batch-two-process-recorded-restart", "spring/batch-killed-worker-recovery", "spring/batch-job-identity", "spring/batch-restart-verification-matrix"]),
    dict(slug="batch-killed-worker-recovery", section="spring/production", checked=True,
        title="Spring Batch killed worker: fence it, recover STARTED, then restart",
        summary="A hard-killed JVM leaves STARTED metadata; a new launcher must not run the same instance until recovery is deliberate.",
        blocks=[
            ("Kill after a known commit", "The child worker pauses while processing source ID 3, after the first two-row chunk commits. The test forcibly terminates that process. Its H2 file retains two business rows and a STARTED JobExecution. A fresh JVM tries the same manifest and receives a running-execution rejection. The persisted state is not guessed from the old process's exit code: the test reads the repository table."),
            ("Make recovery conditional", "Only after the test has waited for the child to die does its recovery path call JobOperator.recover on that STARTED execution. The same identifying parameters then complete IDs 1 through 4. The repository holds one JobInstance and two executions. In a deployed scheduler, a process check alone is insufficient if another host can still own the lease; fence the old worker and inspect [[spring/batch-input-snapshot|the source version]] first."),
            ("Respect the limit", "The fixture kills a process between chunks, not in the middle of a database commit. It uses H2 file storage and a key-based writer. It does not establish how a remote database, broker send or distributed lease behaves in the write/metadata race. [[spring/batch-restart-verification-matrix|The test matrix]] leaves those windows open.")],
        code='JobExecution stale = jobExplorer.getLastJobExecution(\n    receiptJob.getName(), manifestParameters);\nif (stale == null || !stale.getStatus().isRunning()) {\n    throw new IllegalStateException("no running execution to recover");\n}\njobOperator.recover(stale);',
        language="java", cost="A process-kill test starts multiple JVMs and persists H2 metadata, so it belongs in an integration tier. Recovery needs human or controller evidence that the prior writer is fenced.",
        mistakes=["Do not call recover while the old worker may still write.", "Do not add a timestamp parameter to bypass STARTED metadata.", "Do not describe a between-chunk kill as coverage of an in-commit crash."],
        related=["spring/batch-jdbc-repository-boot4", "spring/batch-running-execution-recovery", "spring/batch-source-digest-guard", "spring/batch-restart-verification-matrix"]),
    dict(slug="batch-source-digest-guard", section="spring/data-transactions", checked=True,
        title="Spring Batch source digest: reject changed rows before a restart",
        summary="A persisted checkpoint is unsafe when the query result or source file changes under the same manifest ID.",
        blocks=[
            ("Bind bytes to identity", "The file-backed fixture hashes its ordered source ID and unit pairs when it first sees a manifest. On a later launch it recomputes the digest before calling the launcher. The test changes ID 4 from 44 to 82 after a failed run. The relaunch is rejected as changed input, leaves the two committed target rows untouched and creates no second Batch execution."),
            ("Use a real snapshot in production", "Hashing a mutable table at launch is a gate, not an immutable source. Another writer could change it after the digest check and before the Batch reader consumes it. Pin a file version, a database snapshot or a versioned staging table. Add the manifest identity, source version, count and digest to a reviewable record; [[spring/batch-input-snapshot|the input guide]] explains why a pathname alone is insufficient."),
            ("Make replay conflicts explicit", "The H2 writer keys output by source ID and can replace a previously written row. The digest prevents this tested changed-source relaunch, but it does not validate every record's provenance or an external side effect. A correction should get a new manifest and a documented relationship to the failed one. [[spring/batch-result-reconciliation|Reconciliation]] must still account for accepted, rejected and unprocessed IDs.")],
        code='String observedHash = sourceHash(jdbc);\nString storedHash = jdbc.query(\n    "SELECT source_hash FROM receipt_manifest WHERE manifest_id = ?",\n    result -> result.next() ? result.getString(1) : null, manifestId);\nif (storedHash != null && !storedHash.equals(observedHash)) {\n    throw new IllegalStateException("source changed for manifest " + manifestId);\n}',
        language="java", cost="Digesting n source rows costs O(n) reading time and a small fixed hash state. Pinning an immutable snapshot adds storage and retention work.",
        mistakes=["Do not treat a digest computed before the read as isolation from concurrent mutations.", "Do not reuse the old manifest ID for corrected input.", "Do not let an upsert hide changed source values."],
        related=["spring/batch-input-snapshot", "spring/batch-idempotent-writer", "spring/batch-killed-worker-recovery", "spring/batch-result-reconciliation"]),
    dict(slug="batch-repository-assertions", section="spring/testing", checked=True,
        title="Spring Batch restart tests: assert metadata rows, not repeated ID values",
        summary="A restart test must prove that successive executions belong to one persisted JobInstance.",
        blocks=[
            ("Count the persisted graph", "The two-JVM fixture checks one row in BATCH_JOB_INSTANCE and two rows in BATCH_JOB_EXECUTION. It also checks the same instance ID in both process outputs. The row counts matter: two fresh in-memory repositories can each allocate ID 1 and make a superficial equality assertion pass. [[spring/batch-jdbc-repository-boot4|The JDBC setup]] is part of the proof."),
            ("Check the negative path", "After a force-killed worker, a new process cannot launch the same manifest while the repository still says STARTED. The test checks that refusal before operator recovery. Another check changes a source row and confirms the digest guard refuses the restart without adding a JobExecution. These failures reveal more than a final COMPLETED assertion."),
            ("Read the business table too", "The first process leaves IDs 1 and 2 committed; the recovered process leaves 1 through 4, once each. Keyed output prevents duplicate IDs but does not prove exactly-once broker delivery. Keep an independent test for any remote side effect and the target database's transaction behavior.")],
        code='assertEquals(1, count(databaseUrl, "BATCH_JOB_INSTANCE"));\nassertEquals(2, count(databaseUrl, "BATCH_JOB_EXECUTION"));\nassertEquals(4, count(databaseUrl, "receipt_import"));',
        language="java", cost="Metadata assertions add a few indexed reads to a slow integration test. They prevent a false positive that can survive status and row-count checks.",
        mistakes=["Do not compare only generated instance ID 1 across fresh processes.", "Do not test only the successful restart path.", "Do not infer exactly-once remote effects from a unique database key."],
        related=["spring/batch-jdbc-repository-boot4", "spring/batch-two-process-recorded-restart", "spring/batch-killed-worker-recovery", "spring/testing-boundaries"]),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {"spring/production": "spring-production", "spring/data-transactions": "spring-data", "spring/testing": "spring-testing"}
for index, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    assert all(target in titles for target in item["related"]), path
    body = paragraph(item["summary"])
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + paragraph(content)
    body += '<h2>Checked excerpt</h2><pre><code class="language-' + item["language"] + '">' + html.escape(item["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and verification</h2>" + paragraph(item["cost"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2><p>" + ", ".join('<a href="/' + target + '">' + html.escape(titles[target]) + "</a>" for target in item["related"]) + ".</p>"
    row = copy.deepcopy(by_path["spring/component-scan-vs-bean"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
        title=item["title"], summary=item["summary"], body=body, subject=subjects[item["section"]],
        tags=["spring", "spring-boot", "spring-batch", item["slug"]], sort_order=4400 + index,
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "framework_version": "Spring Boot 4.0.8; Spring Batch 6.0.5 source-kit target",
        "java_version": "21 source-kit target", "verification_suite": "TwoProcessRestartContractTest",
        "download_path": "/downloads/aitrove-spring-source-kit.zip",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    rows.append(row)
    by_path[path] = row

for section in subjects:
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    if paths:
        hub = by_path[section]
        hub["data"]["modules"].append({"title": "Batch metadata and hard-stop recovery",
            "summary": "Check the actual repository, input snapshot and recovery decision.", "lessons": paths})
        hub["body"] += "<h2>Batch metadata and hard-stop recovery</h2><ul>" + "".join(
            '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths) + "</ul>"
        hub["updated_at"] = stamp

def replace(path, old, new):
    row = by_path[path]
    assert old in row["body"], (path, old[:70])
    row["body"] = row["body"].replace(old, new)
    row["updated_at"] = stamp

replace("spring/batch-running-execution-recovery",
    "The source kit does not force-kill a process, so this remains a design boundary.",
    "The source kit now force-kills one H2 worker between chunks, proves a same-manifest relaunch is blocked, and calls JobOperator.recover after the worker is confirmed dead. <a href=\"/spring/batch-killed-worker-recovery\">That checked path</a> does not cover the in-commit race or a distributed lease.")
replace("spring/batch-running-execution-recovery",
    "A controlled integration test can stop the worker after a committed chunk, restart the application, and assert that recovery does not run alongside the old process.",
    "The checked integration test stops a worker after a committed chunk, confirms the process has exited, and verifies that an unchanged launch is refused before recovery.")
replace("spring/batch-input-snapshot",
    "The current kit does not mutate source rows between launches; this policy still needs an integration test.",
    "The checked kit now mutates ID 4 after failure and rejects the same-manifest restart before a new Batch execution is created. <a href=\"/spring/batch-source-digest-guard\">The digest test</a> remains a gate against change at launch, not an immutable database snapshot.")
replace("spring/batch-restart-verification-matrix",
    "None of these cases is covered by file-backed H2 after an orderly FAILED state.",
    "The source kit now covers a hard kill between chunks, STARTED-state refusal, explicit recovery and changed-input rejection on H2. A kill during a business write, the metadata race, target-database semantics and a distributed fencing test remain open.")
replace("spring/batch-restart-verification-matrix",
    "Another suite should replace or reorder source input between attempts and prove that the manifest guard rejects it.",
    "The H2 suite changes one source row and proves its digest guard rejects the restart. A target-database suite should test changes during the read and across replicas.")
replace("spring/batch-restart-verification-matrix",
    "The source kit now has an in-process chunk restart and a separate two-JVM run after FAILED was recorded.",
    "The source kit now has an in-process chunk restart, a two-JVM run after FAILED was recorded and an abrupt-death recovery path with a JDBC JobRepository.")
replace("spring/batch-two-process-recorded-restart",
    '<a href="/spring/batch-running-execution-recovery">an orphaned STARTED execution</a> and the business-write/metadata-commit race are not.',
    "<a href=\"/spring/batch-killed-worker-recovery\">The orphaned STARTED execution</a> is now checked separately; the business-write/metadata-commit race is not.")
replace("spring/batch-two-process-recorded-restart",
    "It sees the same JobInstance ID, completes the job, and leaves exactly IDs 1, 2, 3 and 4 in the target.",
    "It sees the same JobInstance ID, completes the job, and leaves exactly IDs 1, 2, 3 and 4 in the target. The test also reads JDBC metadata: one persisted JobInstance and two executions. <a href=\"/spring/batch-jdbc-repository-boot4\">Repository configuration</a> matters because matching numeric IDs alone can mislead.")
replace("spring/batch-durable-restart-check",
    "while an abrupt process kill remains untested.",
    "and now also checks a forced kill between chunks with explicit operator recovery.")
replace("spring/batch-durable-restart-check",
    "A process killed before repository status is updated may leave STARTED metadata. Relaunch can be refused until the old worker is fenced and the execution is reconciled.",
    "The checked forced kill leaves STARTED metadata. The next same-manifest relaunch is refused until the test confirms the old worker is dead and calls JobOperator.recover. <a href=\"/spring/batch-killed-worker-recovery\">The recovery lesson</a> gives the observed boundary.")
replace("spring/batch-durable-restart-check",
    "Neither is established by the checked two-JVM case.",
    "The H2 kit checks a between-chunk hard stop and a changed-input rejection; it does not prove an in-commit crash, production database or distributed fencing behavior.")
replace("spring/batch-durable-restart-check",
    "Target-database locking, a hard kill and source replacement remain unproved.",
    "The separate H2 checks now cover a hard kill after a committed chunk and changed-source rejection. Target-database locking and an in-commit crash remain unproved.")
replace("spring/batch-chunk-restart",
    "This is an in-process H2 check, not a process-crash recovery test.",
    "That assertion is in-process; <a href=\"/spring/batch-killed-worker-recovery\">the separate JDBC fixture</a> checks a hard kill between chunks and explicit recovery.")
replace("spring/batch-job-identity",
    "That assertion uses one H2 process. Recovery after a process crash needs a durable JobRepository and stable access to the original input.",
    "That assertion uses one H2 process. The separate <a href=\"/spring/batch-jdbc-repository-boot4\">JDBC repository fixture</a> now proves one persisted instance across two processes; <a href=\"/spring/batch-source-digest-guard\">its digest guard</a> rejects a changed source before restart.")

for row in rows:
    for related in row.get("data", {}).get("related", []):
        if related.get("path") in titles:
            related["title"] = titles[related["path"]]

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "articles; Spring article total:",
    sum(row["path"].startswith("spring/") and row["type"] == "article" for row in rows))

"""Add original database operations lessons to the Web Development fixture."""
import copy
import datetime
import html
import json
import re
import subprocess
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def paragraph(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/database-capacity-and-online-change-operations"
hub_title = "Database Capacity and Online Change Operations"
topics = [
    dict(
        slug="connection-pool-budgets-and-queue-admission",
        title="Connection Pool Budgets and Queue Admission",
        summary="Budget connections across application instances and bound waiting before the database reaches its limit.",
        concept="A connection pool is a concurrency limit, not a source of unlimited database capacity. Each application process can hold its own pool, while the database has a finite connection ceiling and reserves some slots for maintenance. The total possible application demand is the sum of every replica, worker, scheduled job, and migration process. When every caller can wait without a deadline, the pool turns a short database slowdown into a memory and latency backlog. Admission must be bounded before the database is saturated. Connection acquisition time, active query time, and time spent waiting on database locks are separate measurements; one average request duration hides the distinction.",
        case="A permit service runs six API replicas, each configured for 29 connections. Two report workers each open 17 more, and an operator reserves 12 slots for maintenance. The resulting possible demand is 220 connections. The database allows 190 ordinary application connections. During a field inspection upload, a remote image processor pauses while holding a transaction and connection. Requests queue behind full pools, application memory rises, and a rollout doubles replica count. The fix starts by counting all owners, setting per-process budgets under the database ceiling, releasing connections before network calls, and placing a short acquisition deadline on the queue.",
        implementation="Write a connection inventory as part of the deployment plan: maximum replicas times API pool size, plus workers, scheduled jobs, migrations, and explicit spare capacity. Ensure autoscaling cannot exceed that envelope without changing the budget. Keep transactions short and acquire the connection close to the query, rather than at the start of a long HTTP request. Put a finite bound on pool waiters and a deadline on acquisition; return an intentional overload response or shed optional work once admission is full. If an intermediary pooler is used, verify whether it pools sessions or transactions, because session state, prepared statements, and temporary tables may behave differently. Keep health checks from consuming the last useful slot. Test an ordinary rollout and a failed region that moves traffic to fewer healthy instances.",
        cost="A smaller pool can reduce database thrash and memory use, but it may cap useful concurrency when queries are short and the database has spare capacity. A larger pool can raise query concurrency while also increasing contention, context switching, and the blast radius of a stalled query. Queueing adds latency before execution; an unbounded queue only postpones the error while using application memory. Track pool active and idle counts, acquisition p95, rejected waiters, database connections, transaction duration, and lock wait time. Multiply by replica count when interpreting every metric. Measure at a known arrival rate instead of choosing a pool size by CPU count alone.",
        failure="Increase API replicas from six to nine without changing their pool size. The aggregate connection ceiling is crossed even though each replica's health check passes. Next, hold one connection across a 47-second image-service call; a burst fills the remaining pools and makes unrelated case reads wait. Kill one region and route its traffic into the survivors while the database limit stays fixed. Verify that admission rejects excess work promptly, maintenance can still connect, and queued requests do not wait beyond their caller deadlines. A pool timeout must be distinguishable from a slow SQL query in telemetry.",
        drill="Set a database application limit of 190, reserve 12 slots, six API replicas at 29 each, and two workers at 17 each. Compute the initial overage. Choose new limits that leave room for one additional API replica during rollout and for emergency access. Run a load test with one intentionally slow query and one slow external call. Capture acquisition time, query time, lock wait, queue length, and rejection count. Then drain a replica and verify that released requests are retried only when the operation permits it.",
        decision="Pool size is a fleet-level capacity decision; waiting needs a budget and an exit path.",
        code='function totalDatabaseSlots(apiReplicas, apiPool, workerReplicas, workerPool, reserved) {\n'
             '  return apiReplicas * apiPool + workerReplicas * workerPool + reserved;\n'
             '}\n'
             'console.log(totalDatabaseSlots(6, 29, 2, 17, 12) <= 190);\n'
             '// Output: false',
        checks=["Fleet-wide maximum stays within the tested database connection ceiling.", "Pool acquisition has a finite deadline and bounded waiting.", "An external service pause does not hold a database connection."],
        mistakes=["Sizing one process pool without multiplying by replicas.", "Treating a pool queue as extra database capacity.", "Keeping a connection during slow network or user work."],
        related=["web-tech/backend-api-systems", "web-tech/load-tests-and-capacity-budgets"],
    ),
    dict(
        slug="transaction-retry-deadlock-and-side-effect-boundaries",
        title="Transaction Retry, Deadlock, and Side-Effect Boundaries",
        summary="Retry the complete database transaction after a retryable conflict without repeating external effects.",
        concept="A database can abort a transaction when concurrent work cannot satisfy its isolation guarantees or when lock acquisition forms a deadlock. The application should treat the aborted transaction as a unit: read the required state again, recompute its decision, and retry the complete set of statements under a bounded policy. Retrying only the last failed SQL statement can preserve a stale business decision. Not every database error is retryable. A uniqueness violation may represent a real conflict, and a timeout may leave uncertainty about whether an earlier operation committed unless the caller checks a stable operation record. External email, payment, and notification effects must not run inside a function that may execute twice.",
        case="Two permit reviewers update cases 47 and 62 in opposite order as they exchange assignments. One transaction locks 47 then asks for 62; the other locks 62 then asks for 47. The database cancels one to break the cycle. A naive handler retries only its second update, retaining an outdated count from the first read, while an email sent before commit reaches the contractor twice. The corrected handler locks records in a consistent order, retries the whole transaction on a recognized conflict with an attempt limit, and writes one outbox intent in the same commit. Delivery workers deduplicate that intent by operation identity.",
        implementation="Choose a stable lock order when a workflow touches more than one row or resource. Keep transactions short and avoid waiting for user input, HTTP requests, or email providers while holding locks. On a serialization or deadlock result, roll back, start a fresh transaction, reread the rows, recompute the authorization and transition, and retry with a small bounded delay. Carry a stable idempotency key across attempts so a lost response after commit can return the recorded operation result. The retry wrapper must classify errors from the actual database driver; avoid a broad catch that retries constraint violations and programming mistakes. Persist outbox intents or equivalent durable work in the transaction, then send externally after commit. Document what the caller sees when the attempt budget is exhausted.",
        cost="Retrying consumes extra reads and writes, and high conflict rates can make throughput collapse under load. Consistent lock ordering reduces one deadlock pattern but cannot remove every conflict. Serializable isolation may catch anomalies that weaker isolation permits, yet conflict tracking and transaction restarts have a real cost. Measure abort rate by cause, attempts per operation, lock wait p95, transaction duration, and outbox duplicate suppression. Bound retry count and total deadline; adding unlimited retries makes a hot record appear slow rather than visibly overloaded. A backoff must fit within the caller's time budget and should not hide a persistent schema or data error.",
        failure="Run two assignment exchanges with reversed record order and confirm a deadlock is detected or prevented, never silently committed with partial state. Force a serialization failure after a read and show that the retry rereads current permission and case status. Fail after a database commit but before the HTTP response; the same idempotency key must return the committed result without a second notification. Return a unique-constraint error unrelated to the retry policy and verify it reaches a domain conflict response. Exhaust the retry budget under a hot case and ensure the handler does not continue in a detached background loop.",
        drill="Create two transactions for reviewers 29 and 47 exchanging case owners. Make each read both cases, check current authorization, update its target, and create one outbox intent. Execute them in the opposite lock order, then again with a stable order. Inject a retryable database conflict on the first attempt and a unique-constraint conflict on another run. Count committed transitions, outbox rows, delivered messages, and retries. Prove that no notification is visible for a rolled-back transaction.",
        decision="Retry a newly evaluated transaction, never a stale fragment or an external side effect.",
        code='function retryDisposition(databaseCode, attempt, maximumAttempts) {\n'
             '  const retryable = databaseCode === "serialization_failure" || databaseCode === "deadlock_detected";\n'
             '  return retryable && attempt < maximumAttempts ? "restart-transaction" : "stop";\n'
             '}\n'
             'console.log(retryDisposition("deadlock_detected", 1, 3));\n'
             '// Output: restart-transaction',
        checks=["Retry begins a new transaction and repeats all reads and decisions.", "External effects are committed as durable intents, then delivered afterward.", "Retry count and total operation time are bounded."],
        mistakes=["Retrying only the statement that raised the conflict.", "Sending an email before a transaction commits.", "Retrying every database error as though it were transient."],
        related=["web-tech/transactions-and-concurrent-writes", "web-tech/background-jobs-and-outbox"],
    ),
    dict(
        slug="resumable-data-backfills-and-reconciliation",
        title="Resumable Data Backfills and Reconciliation",
        summary="Move old rows to a new representation in bounded chunks while concurrent writes continue.",
        concept="A backfill copies or computes a new representation for existing records after an application begins supporting it. Unlike a one-time migration in an empty environment, a live backfill competes with user reads and writes and may be interrupted midway. A checkpoint says where one worker has progressed; it does not by itself prove that rows changed concurrently are correct. The job must be idempotent, use a stable traversal key, keep each transaction bounded, and reconcile against the authoritative record before switching readers. The write path must preserve both old and new representations, or capture changes through a proven update stream, throughout the migration window.",
        case="The permit service replaces a free-text inspection duration with an integer minute field. There are 2.7 million old cases. A single update transaction locks too much and generates a large recovery log, so an operator processes 470 rows per chunk by immutable case ID. During the run, reviewer 62 edits case 47, which lies behind the current checkpoint. A high-water mark alone would miss that edit. The application writes the new field for current changes; the backfill updates only rows that still need conversion, stores its checkpoint after each committed chunk, and runs a final reconciliation before any reader stops accepting the old form.",
        implementation="Deploy readers that tolerate both representations and writers that keep the new field correct before launching the historical job. Choose an immutable, indexed traversal key, record the last committed key, and fetch the next bounded batch in key order. The conversion must be repeatable: rerunning a chunk should not double a numeric value or overwrite a newer user edit. Use a conditional update or row version check so work based on an old snapshot cannot replace a concurrent change. Commit a chunk and its checkpoint together where possible; otherwise design for replay of the last chunk. Throttle based on replica lag, lock waits, and application latency. After the first pass, reconcile nulls, mismatches, and rows created or modified during the run before making the new field mandatory.",
        cost="A backfill reads O(N) records and may write O(N) rows, with additional index maintenance and recovery-log traffic. A chunk of 470 rows is an initial budget, not a universal optimum: the right size depends on row width, write rate, lock behavior, and replication capacity. More workers can shorten wall time while increasing contention and duplicate scanning. Track rows visited, rows changed, chunk time, error rate, last checkpoint, outstanding mismatches, database load, and replica lag. Do not declare completion from a counter of processed keys alone; the final invariant is data agreement for every record the new reader may use.",
        failure="Kill the worker after writing a chunk but before its checkpoint is persisted. On restart it must repeat safely and reach the same stored value. Edit a processed case behind the high-water mark while the job continues; the write path or reconciliation must restore agreement. Create a new case below an assumed numeric range by importing a legacy ID and check that it is not skipped. Force one malformed duration and route it to a reviewable exception set rather than halting every later chunk. Raise replica lag above the agreed limit and confirm the job slows or stops without delaying foreground permit review.",
        drill="Start with cases 29, 47, 62, and 91 and a checkpoint before 47. Convert at most two rows per transaction. Crash after the first commit, replay, then edit case 29 and insert a late legacy case. Reconcile the old and new duration fields and list any row that cannot be converted without a business rule. Record an acceptance threshold for mismatches, a pause threshold for latency or lag, and the evidence required before the old field can be removed.",
        decision="A resumable checkpoint tracks progress; only write-path coverage and reconciliation prove correctness.",
        code='function nextBackfillKeys(caseIds, lastCommittedCaseId, chunkLimit) {\n'
             '  return caseIds.filter(caseId => caseId > lastCommittedCaseId).sort((left, right) => left - right).slice(0, chunkLimit);\n'
             '}\n'
             'console.log(nextBackfillKeys([91, 29, 62, 47], 29, 2).join(","));\n'
             '// Output: 47,62',
        checks=["Chunk replay is idempotent after a crash.", "Concurrent edits behind the checkpoint reach the new representation.", "Final reconciliation counts unresolved mismatches before reader cutover."],
        mistakes=["Using offset pagination while the source keeps changing.", "Calling a high-water mark a complete correctness check.", "Running one unbounded write transaction against a live table."],
        related=["web-tech/expand-and-contract-migrations", "web-tech/replica-lag-read-your-write-and-version-cursors"],
    ),
    dict(
        slug="online-index-builds-and-query-plan-release-gates",
        title="Online Index Builds and Query Plan Release Gates",
        summary="Stage large index changes with write-availability checks, validity checks, and measured query plans.",
        concept="An index can make a selective query cheaper, but building or maintaining it costs storage, writes, and operational time. On a populated table, a conventional build may block writes; some databases provide an online or concurrent form with distinct constraints. The availability label is not a guarantee of zero impact: the build scans data, consumes I/O, waits on other transactions, and may fail. A failed concurrent build can leave an invalid artifact that still occupies resources. Query planners also choose among paths based on statistics and parameters, so an index definition alone does not prove the intended endpoint improved.",
        case="The permit queue filters by organization, review state, and newest case ID. The current query scans millions of rows at the morning peak. A migration adds an index during the same release as a new queue page; staging passes because its table is tiny, while production write latency rises and the build stalls behind a long-running transaction. The release plan separates index deployment from reader rollout, checks database-specific concurrent-build rules, monitors progress and validity, refreshes statistics where needed, and compares actual plans for representative tenants before allowing the queue page to depend on the new path.",
        implementation="Start with the endpoint predicate, sort order, result limit, and tenant isolation rule, then design the index against real query shapes rather than every column in the table. Capture plans and execution times for small and large tenants. For PostgreSQL, a concurrent index build permits ordinary table writes while scanning, but it cannot run inside a transaction block and can leave an invalid index after failure; other engines have different rules. Confirm the migration runner's transaction behavior before deployment. Monitor build progress, lock waits, write latency, storage growth, and replica lag. Validate the finished index, verify the planner uses it where useful, then release the dependent query. Have a safe cleanup step for failed artifacts and a rollback that does not assume dropping an index is free.",
        cost="An index lookup for a selective bounded query can avoid a full table scan, but the exact runtime depends on cardinality, visibility, disk state, and the chosen plan. Every insert or update that changes indexed keys adds maintenance work, and an extra index consumes storage on primary and replicas. Building online may take longer than an exclusive build and still compete for I/O. A wide index with many included fields can reduce heap visits while increasing write and cache cost. Measure p95 queue latency, rows scanned versus returned, buffer reads, write latency, build duration, and disk headroom. Keep the index only when the measured workload earns its ongoing cost.",
        failure="Run the migration runner with its default transaction wrapper and confirm a concurrent build is rejected before release rather than halfway through deployment. Cancel a build and inspect for an invalid leftover index; clean it up according to the database's supported procedure. Start a long transaction before a build and record the wait stage. Compare a small tenant and a large tenant after statistics change; the planner may choose different routes. Add the queue page before the index is valid and verify the feature gate prevents a sudden full-table scan at peak traffic.",
        drill="For a queue of 2.7 million cases, write the predicate for organization 47 with review state open, sorted by newest case ID and capped at 63 results. Plan an index rollout separately from the application query release. Record the old plan and a large-tenant plan, migration transaction setting, progress signal, validity check, write-latency ceiling, disk reserve, and cleanup action after cancellation. Enable the page only when the index exists, is valid, and the intended query plan meets the task budget under representative data.",
        decision="An index becomes part of the release only after its build, validity, and real query benefit are observed.",
        code='function indexReleaseReady(indexValid, largeTenantP95Ms, latencyBudgetMs, writeP95Ms, writeBudgetMs) {\n'
             '  return indexValid && largeTenantP95Ms <= latencyBudgetMs && writeP95Ms <= writeBudgetMs;\n'
             '}\n'
             'console.log(indexReleaseReady(true, 47, 63, 91, 80));\n'
             '// Output: false',
        checks=["Migration runner supports the chosen build mode and its transaction rules.", "Failed builds are detected and invalid artifacts have a cleanup procedure.", "Representative query plans and write latency pass before reader rollout."],
        mistakes=["Assuming online means no I/O or lock impact.", "Deploying an index and dependent query in one unguarded step.", "Checking index existence without validity or actual plan evidence."],
        related=["web-tech/indexes-and-query-plans", "web-tech/expand-and-contract-migrations"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
hub.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)),
    path=hub_path,
    title=hub_title,
    summary="Budget database connections, retry conflicts safely, backfill live data, and release indexes with measured gates.",
    sort_order=3610,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
hub["data"] = {
    "subject_root": "web-tech/web-technology",
    "section_path": hub_path,
    "content_format": "html",
    "seo_ready": False,
    "modules": [],
    "resource_tabs": [
        {"title": "Web Development", "path": "web-tech/web-technology"},
        {"title": "Projects", "path": "web-tech/web-technology/project"},
        {"title": "Quizzes", "path": "web-tech/quizzes"},
    ],
}
entries.append(hub)
by_path[hub_path] = hub

for number, topic in enumerate(topics):
    path = "web-tech/" + topic["slug"]
    assert path not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
        path=path,
        title=topic["title"],
        summary=topic["summary"],
        sort_order=3611 + number,
        created_at=stamp,
        updated_at=stamp,
        published_at=stamp,
    )
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + paragraph(topic["cost"]) + "<h2>Failure trace</h2>" + paragraph(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + paragraph(topic["drill"]) + "<h2>Decision note</h2>" + paragraph(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
    entry["body"] = body
    entry["data"] = {
        "subject_root": "web-tech/web-technology",
        "section_path": hub_path,
        "content_format": "html",
        "seo_ready": False,
        "kind": "tutorial",
        "author_path": "authors/aitrove-editorial",
        "reading_minutes": 8,
        "related": related,
    }
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path["web-tech/" + topic["slug"]]
    entry["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in entry["data"]["related"]) + ".</p>"

hub["data"]["modules"] = [{"title": hub_title, "summary": hub["summary"], "lessons": ["web-tech/" + topic["slug"] for topic in topics]}]
hub["body"] = paragraph("Production data changes happen while users and workers continue writing. This track follows a permit service through connection admission, transaction conflicts, a historical backfill, and an index build. Each operation has a measurable stop condition and a recovery path.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/data-persistence", "web-tech/transactions-and-concurrent-writes", "web-tech/expand-and-contract-migrations"]) + ".</p>"
root_entry = by_path["web-tech/web-technology"]
root_entry["data"]["modules"].append({"title": hub_title, "summary": hub["summary"], "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
root_entry["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
root_entry["updated_at"] = stamp
crosslinks = {
    "web-tech/data-persistence": [hub_path],
    "web-tech/transactions-and-concurrent-writes": ["web-tech/transaction-retry-deadlock-and-side-effect-boundaries"],
    "web-tech/expand-and-contract-migrations": ["web-tech/resumable-data-backfills-and-reconciliation", "web-tech/online-index-builds-and-query-plan-release-gates"],
    "web-tech/indexes-and-query-plans": ["web-tech/online-index-builds-and-query-plan-release-gates"],
    "web-tech/load-tests-and-capacity-budgets": ["web-tech/connection-pool-budgets-and-queue-admission"],
}
for path, targets in crosslinks.items():
    assert path in by_path, path
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4, "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))

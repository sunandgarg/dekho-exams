"""Add database change-stream and recovery-boundary lessons to the DevOps preview."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
course = "devops/devops-tutorial"
project_hub = course + "/project"
quiz_hub = "devops/quizzes"
specs = []


def lesson(slug, title, summary, definition, operation, language, sample, cost, mistakes, related):
    path = "devops/" + slug
    assert path not in by_path, path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      operation=operation, language=language, sample=sample,
                      cost=cost, mistakes=mistakes, related=related))


lesson(
    "replication-slot-wal-budget", "Replication slots: bound retained WAL before a consumer outage fills the disk",
    "Measure each slot's restart position and decide whether replay or resnapshot is safe.",
    "A PostgreSQL replication slot retains log records that a replica or logical consumer may still need. When a consumer stops advancing, the oldest required WAL position can stay fixed while writes continue, increasing disk use. A retention ceiling can protect the primary's disk, but if required WAL is discarded the consumer may be unable to resume from its prior position. Dropping a slot relieves retention at the cost of that replay path.",
    "A receipt change-feed connector is offline during a promotion weekend. Query slot activity, restart_lsn, confirmed_flush_lsn, wal_status, and bytes between the current WAL position and each slot's restart position. The SQL is read-only and targets a PostgreSQL version that exposes those columns. Compare retained bytes with free storage, current WAL generation rate, and the expected repair time; an absolute byte count without a growth rate gives no time-to-full estimate. Restore the connector if its offset and slot still align, then verify event counts and a receipt marker across the catch-up window. If the slot is lost or the consumer offset no longer exists in WAL, stop the connector and plan a controlled resnapshot with sink deduplication before deleting the old slot. Never drop an apparently inactive slot just because its client process is absent; it may be the only path to unconsumed changes. Record the ownership and recovery decision for every slot.",
    "sql", "SELECT slot_name, slot_type, active, restart_lsn, confirmed_flush_lsn, wal_status,\n       pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS retained_bytes\nFROM pg_replication_slots\nORDER BY retained_bytes DESC NULLS LAST;",
    "WAL retention buys recovery time but spends disk. A strict cap protects the primary while increasing the chance of resnapshot and downstream reconciliation. Queries over slot metadata are cheap relative to a full table scan, but regular alerting should include disk headroom and write rate. A consumer appearing connected does not prove its confirmed position is moving. Recheck downstream business effects after catch-up, not only slot activity.",
    ["Do not drop an inactive slot before identifying its consumer and offset.", "Do not use free disk bytes alone without WAL growth rate and repair time.", "Do not call a reconnected consumer recovered until its sink catches up."],
    ["devops/replica-lag-read-contract", "devops/backup-and-recovery", "devops/node-pressure-eviction", "devops/observability-signals"],
)

lesson(
    "cdc-snapshot-stream-handoff", "CDC snapshot handoff: prove that initial rows and later changes form one history",
    "Coordinate snapshot position, stream offset, and sink idempotency.",
    "Change-data capture often begins with a table snapshot and then reads the database log from a recorded position. The two phases must cover changes made while the snapshot runs without a gap. A restart before snapshot completion may cause rows to be emitted again; a failover can change which log positions remain available. The downstream sink therefore needs stable keys and a repeatable upsert or deduplication rule.",
    "A claims search index is rebuilt from PostgreSQL while new claims keep arriving. Record connector configuration, table set, snapshot completion marker, source log position, and sink checkpoint before starting. Apply snapshot records by claim ID and version, then stream updates from the connector's supported handoff point; do not start the stream at a guessed wall-clock time. Inject an update and a delete while the snapshot scans, then stop the connector immediately before it records completion. On restart, verify the final search index matches a bounded source query and that no claim is missing or resurrected. For a primary failover, compare the connector's saved offset with the new source's slot position before allowing it to publish more events. If the required history is unavailable, rebuild from a new snapshot rather than silently skipping to the current log. Preserve an audit record of source row count, sink row count, and sampled content hashes at the acceptance boundary.",
    "text", "Claims CDC handoff record\nSource tables and schema revision: captured\nSnapshot: completed marker and source log position\nSink key: claim ID plus monotonic row version\nRestart test: update and delete during snapshot; no gap or resurrection\nFailover gate: saved offset is available on new source\nAcceptance: bounded source and sink reconciliation matches",
    "A consistent snapshot can consume I/O and retain old row versions while it runs. Deduplicating writes adds sink storage and CPU but makes replay safe. Large table scans should be paced against user latency and replication pressure. A count match can hide wrong rows, so compare identifiers and sampled values too. An offset advancing without a sink checkpoint is not proof that downstream data is durable.",
    ["Do not choose a CDC start point by wall-clock guesswork.", "Do not assume a restart will never repeat snapshot rows.", "Do not advance past an unavailable offset without an explicit rebuild plan."],
    ["devops/replication-slot-wal-budget", "devops/event-schema-evolution", "devops/database-backfill-checkpoints", "devops/failover-write-fencing"],
)

lesson(
    "transactional-outbox-delivery", "Transactional outbox: commit business state and event intent together",
    "Separate atomic database intent from later at-least-once publication.",
    "A service that writes a database row and publishes a message as separate actions can fail between them. The database may commit while no event is sent, or an event may be sent before the database write is durable. An outbox row inserted in the same database transaction as the business change closes that local gap. A dispatcher still may publish the event twice if it crashes after sending but before recording progress, so consumers must guard their effects with the event ID.",
    "A payout API changes a payout from pending to settled. In one PostgreSQL transaction, update the payout only if it is pending and insert an outbox event only for the row that actually changed. The SQL fragment assumes the tables, event ID uniqueness, and status constraint already exist; execute it against a disposable database first. A CDC connector or polling dispatcher reads committed outbox rows, publishes the event, and checkpoints its source position. Crash the dispatcher after publish but before checkpoint: the same event may be published again, and the consumer must record its event ID before applying an irreversible downstream effect. Then crash the API before transaction commit: neither payout state nor outbox intent should appear. Monitor oldest unpublished event age and compare business transitions with emitted event IDs. Deleting outbox rows requires a retention rule tied to confirmed downstream processing and replay needs, not merely the passage of a few hours.",
    "sql", "BEGIN;\nWITH settled AS (\n  UPDATE payouts\n  SET status = 'settled'\n  WHERE payout_id = 47 AND status = 'pending'\n  RETURNING payout_id\n)\nINSERT INTO payout_outbox (event_id, payout_id, event_type)\nSELECT 'payout-47-settled', payout_id, 'PayoutSettled' FROM settled\nON CONFLICT (event_id) DO NOTHING;\nCOMMIT;",
    "The outbox adds writes, storage, a dispatcher, and retention work. In return it makes event intent durable with the business transition. A fast publisher can still outpace a slow consumer; size broker retention and replay capacity accordingly. The unique event ID protects only the outbox row unless every effectful consumer enforces its own deduplication. Measure oldest event age and downstream completion, not only publish success.",
    ["Do not publish an event before the business transaction commits.", "Do not claim exactly-once delivery merely because the outbox insert is atomic.", "Do not purge event rows before the replay and reconciliation window closes."],
    ["devops/queue-consumer-reliability", "devops/queue-visibility-lease", "devops/event-schema-evolution", "devops/retry-amplification-control"],
)

lesson(
    "concurrent-index-build-check", "Concurrent index builds: verify validity after the command exits",
    "Keep writes available while accounting for extra scans and failed-index cleanup.",
    "PostgreSQL can build an index concurrently so ordinary table writes continue during most of the operation. It performs more work than a regular index build, waits for relevant transactions, and cannot run inside a transaction block. A failed concurrent build can leave an invalid index object, and a unique concurrent build may start enforcing uniqueness before it becomes valid for queries.",
    "A receipt table needs an index for customer history queries. Rehearse the build against a production-like copy with measured row count, write rate, free disk, replication lag, and representative long transactions. Run the statement as its own migration step, outside the framework's automatic transaction wrapper. The SQL includes a read-only catalog check for the index's validity. After completion, inspect pg_index.indisvalid, query plan, write latency, disk use, and replica catch-up before declaring success. If the build fails, identify whether the remaining index is invalid and follow a reviewed drop-and-retry procedure; do not blindly rerun a command under the same name. For a unique index, inspect duplicate data and user-visible uniqueness errors as part of the rollout. Pause another concurrent build on the same table until this one finishes. A low-traffic window reduces contention but does not make the operation free of I/O cost.",
    "sql", "CREATE INDEX CONCURRENTLY receipt_customer_created_idx\nON receipts (customer_id, created_at);\nSELECT c.relname, i.indisvalid, i.indisready\nFROM pg_class AS c\nJOIN pg_index AS i ON i.indexrelid = c.oid\nWHERE c.relname = 'receipt_customer_created_idx';",
    "Extra table scans and index writes consume CPU, I/O, and storage; replicas must apply the resulting changes. A concurrent build lowers write blocking but can run longer than a regular build. An invalid index can still consume space and update work, so it needs a recorded cleanup decision. Keep build duration, lock waits, replica lag, query plan, and transaction error rate in the acceptance record.",
    ["Do not wrap CREATE INDEX CONCURRENTLY in a migration transaction.", "Do not equate command completion with a valid usable index without checking catalog state.", "Do not ignore a failed unique build that may still affect writes."],
    ["devops/database-change-safety", "devops/database-backfill-checkpoints", "devops/replica-lag-read-contract", "devops/ddl-lock-budget"],
)

lesson(
    "ddl-lock-budget", "DDL lock budget: fail a migration before it stalls production traffic",
    "Set a short lock wait and a separate statement deadline for schema changes.",
    "A schema statement may need a strong table lock even when the metadata change itself is quick. If it waits behind a long transaction, later user queries can queue behind the pending DDL and create an outage. A session-local lock_timeout can make the migration fail quickly instead. A separate statement_timeout bounds the total execution time after it acquires the lock.",
    "A claims deployment adds a nullable column. Inspect active transactions and lock waits before the release, then run the DDL in a transaction with a lock wait shorter than the total statement deadline. The SQL is a disposable-environment fragment; choose thresholds from observed traffic rather than copying the sample blindly. Inject a long reader transaction that holds a conflicting lock and prove the migration aborts within its budget while existing user work continues. Retry only after identifying the blocker and scheduling a safer window. If the DDL succeeds, deploy code that tolerates both old and new schema during rollout and rollback. Keep a migration ledger with attempted time, lock wait, result, and revision. Do not set a cluster-wide lock timeout for convenience, since it would change unrelated sessions. A successful ALTER TABLE does not prove the subsequent application version can use the new field correctly.",
    "sql", "BEGIN;\nSET LOCAL lock_timeout = '1200ms';\nSET LOCAL statement_timeout = '45s';\nALTER TABLE claims ADD COLUMN review_batch_id bigint;\nCOMMIT;",
    "A short lock budget may require several attempts, adding release time. A long budget can block application requests behind pending DDL. The total statement deadline prevents unexpectedly expensive work after lock acquisition. Observe waiting and blocking sessions, user query latency, and migration failures as separate signals. Keep the rollback path compatible with the added column and avoid a destructive schema reversal under incident pressure.",
    ["Do not treat a quick metadata operation as free of lock risk.", "Do not set lock_timeout equal to or above the total statement deadline.", "Do not change every session's timeout to protect one migration."],
    ["devops/database-change-safety", "devops/database-backfill-checkpoints", "devops/concurrent-index-build-check", "devops/observability-signals"],
)

lesson(
    "vacuum-horizon-pressure", "Vacuum horizon: find transactions holding old row versions alive",
    "Diagnose bloat from transaction age before forcing a table rewrite.",
    "PostgreSQL keeps old row versions while a transaction may still need to see them. A long transaction, an idle session left inside a transaction, or a replication slot can prevent cleanup from advancing. Autovacuum may run yet fail to reclaim the rows the workload expects. A forced table rewrite can use substantial disk and strong locks; it is not the first response to a growing table.",
    "A payment ledger receives frequent status updates and its table size rises. Inspect pg_stat_activity for old transactions and idle-in-transaction sessions, pg_stat_all_tables for dead tuples and vacuum activity, and replication-slot positions for retained history. The SQL reads only session and table statistics; exact visibility depends on database privileges. Correlate growth with row churn and query latency. Find the owner of an old session before terminating it, since it may contain an unfinished business operation. Fix the application transaction scope or timeout in a test environment, then watch the vacuum horizon advance and dead tuple estimates fall under normal autovacuum. If disk pressure is already acute, use a documented capacity and maintenance plan; do not run VACUUM FULL on the hot ledger merely because it promises a smaller file. Track transaction age and freeze risk as well as bytes, because write availability can be threatened long before an operator notices a table-size chart.",
    "sql", "SELECT pid, state, now() - xact_start AS transaction_age, wait_event_type\nFROM pg_stat_activity\nWHERE xact_start IS NOT NULL\nORDER BY xact_start LIMIT 20;\nSELECT relname, n_dead_tup, last_autovacuum\nFROM pg_stat_all_tables\nWHERE relname = 'ledger_entries';",
    "Longer snapshots can improve an analytical report but make row cleanup and storage more expensive. More frequent vacuum work uses I/O, while too little maintenance allows bloat and freeze pressure to build. A single dead-tuple estimate is approximate; compare trend, transaction blockers, and query behavior. Resolving a blocker does not instantly return disk space to the operating system, so size headroom and verify the steady-state growth rate.",
    ["Do not run VACUUM FULL as the first response to a hot-table size increase.", "Do not terminate an old transaction without identifying its owner and effect.", "Do not assume an autovacuum start time means cleanup is advancing."],
    ["devops/database-pool-pressure", "devops/replication-slot-wal-budget", "devops/node-pressure-eviction", "devops/capacity-load-testing"],
)

lesson(
    "partition-retention-handoff", "Partition retention: detach, prove the archive, then delete",
    "Separate a routing change from irreversible removal of old data.",
    "A partitioned table can retire a time range by detaching or dropping its partition. This is faster than deleting rows one at a time, but it changes query reachability for every row in that range. Retention rules, legal holds, downstream readers, and backup copies must be checked before a partition is removed. A detached partition still occupies storage and may need explicit access controls.",
    "An audit service keeps online records for eighteen months and archives older monthly partitions. Build a manifest containing partition name, date bounds, row count, checksum sample, active hold flags, and expected archive object. Disable new writes into the retiring range, then detach the partition through the version-appropriate PostgreSQL procedure in a maintenance window. The text contract deliberately leaves the actual destructive SQL to an approved migration because the target partition and lock behavior depend on the environment. Verify the archive can be restored and queried in an isolated database before scheduling the detached table for deletion. Check that no query or downstream CDC consumer still depends on the former parent-table route. If a hold is found, stop at the detached state and preserve access under the hold policy. Record a second approval for deletion after the rollback window ends. A completed export job is not proof that its data is complete or restorable.",
    "text", "Audit partition retirement gate\nPartition: exact month and bound manifest\nPrecondition: no new writes and no active hold\nDetach: approved migration, lock and query impact observed\nArchive: row count, digest sample, restore and query pass\nDelete: separate decision after rollback window and reader audit",
    "Keeping detached partitions and archive copies costs storage. Dropping too early can make a lawful or operational restore impossible; keeping everything online can raise query planning and maintenance cost. Detach and drop have different lock behavior, which varies by PostgreSQL version and method. Measure user query latency during the change and confirm the parent table no longer routes to the retired range. A retention calendar is a scheduling input, not deletion authorization by itself.",
    ["Do not drop a partition before verifying its archive can be restored.", "Do not overlook legal holds or consumers that still read the old range.", "Do not assume detaching a partition also frees its storage."],
    ["devops/immutable-backup-retention", "devops/backup-and-recovery", "devops/event-schema-evolution", "devops/database-change-safety"],
)

lesson(
    "pitr-timeline-acceptance", "Point-in-time recovery: accept a restored timeline only after business reconciliation",
    "Test base backup, WAL continuity, target position, and post-recovery reads.",
    "Point-in-time recovery combines a base backup with archived write-ahead log records to restore a database to a chosen boundary. Recovery can branch onto a new timeline; the branch has its own later history. A server starting successfully does not prove it stopped before an unwanted transaction, included every intended earlier transaction, or has the keys and application version needed to serve users.",
    "A ledger operator must recover to just before a mistaken bulk update. In an isolated environment, identify the target by an approved transaction marker or precise recovery position, preserve the original cluster and WAL archive, and restore a base backup with every required log segment and timeline history. The text record lists the evidence to collect without offering a copy-and-paste production restore command. After recovery, query a known good payout immediately before the target and the mistaken update immediately after it; the first must exist and the second must be absent. Compare a bounded list of acknowledged external payments with the restored ledger, because transactions committed after the target may need separate reconciliation. Record the new timeline ID and fence the old writer before any traffic shift. Rebuild replicas and CDC connectors against the new timeline and their actual retained offsets; do not assume their old slots can continue. Finally run a synthetic settlement with the intended application version and encryption keys. If any log segment is missing, report the last proven recovery point rather than implying the target was reached.",
    "text", "Ledger PITR acceptance record\nBase backup ID and required WAL range: verified\nTarget transaction marker and recovered timeline: recorded\nBefore-target payout: present; mistaken update: absent\nPost-target acknowledged effects: reconciled separately\nOld writer: fenced; replicas and CDC: rebuilt or verified\nSynthetic settlement: passed with intended keys and app version",
    "A tighter recovery-point objective needs more frequent WAL archiving and storage. Repeated restore drills consume compute but expose missing files, keys, or incompatible application versions before an incident. A branch timeline complicates later restore choices; retain the history files and name the chosen branch. Measure actual restore time and the count of acknowledged effects after the target. Do not silently reintroduce the bad transaction by replaying an unreviewed downstream queue.",
    ["Do not declare recovery complete because PostgreSQL starts.", "Do not ignore acknowledged external effects committed after the chosen target.", "Do not reconnect the old writer or CDC slot without timeline and ownership checks."],
    ["devops/backup-and-recovery", "devops/failover-write-fencing", "devops/replication-slot-wal-budget", "devops/immutable-backup-retention"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/data-continuity-recovery-project"
quiz_path = "quizzes/devops-data-continuity-decisions"
titles[project_path] = "Project: recover a database change stream and restore boundary"
titles[quiz_path] = "DevOps data continuity decisions"
for item in specs:
    assert all(path in titles for path in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


for heading, summary, slugs in [
    ("Change streams and durable event intent", "Budget retained WAL, hand a snapshot into streaming, and publish committed state safely.", ["replication-slot-wal-budget", "cdc-snapshot-stream-handoff", "transactional-outbox-delivery"]),
    ("Online schema and storage maintenance", "Control index work, DDL waits, vacuum pressure, and partition retirement.", ["concurrent-index-build-check", "ddl-lock-budget", "vacuum-horizon-pressure", "partition-retention-handoff"]),
    ("Restore timeline acceptance", "Prove the selected recovery point against business effects.", ["pitr-timeline-acceptance"]),
]:
    paths = ["devops/" + slug for slug in slugs]
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "operations"],
               sort_order=19800 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
                   f"<p>{html.escape(item['operation'])}</p>"
                   f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
                   f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
                   + "<h3>Common Mistakes</h3><ul>"
                   + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
                   + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]]))
    rows.append(row)

project_related = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Reconcile a CDC snapshot, outbox replay, online schema change, archive, and PITR target.",
               difficulty="Advanced", sort_order=19890,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Run this exercise in a disposable PostgreSQL environment with synthetic payouts, a change-feed connector, an outbox dispatcher, and a search sink keyed by stable business IDs. Take a restorable base backup before injecting faults. Capture initial WAL generation rate, replication-slot positions, sink checkpoint, oldest outbox age, active transaction ages, and disk headroom. Keep the experiment separate from a shared or production database.</p>"
    "<h2>Interrupt the change stream</h2><p>Pause the connector while payouts continue, then calculate retained WAL growth and the time remaining before the disk budget is exhausted. Resume it before its slot is lost and reconcile source and sink IDs. Rebuild a second sink with a snapshot while one payout updates and another is deleted; crash the connector just before it records snapshot completion. After restart, the sink must have neither missing nor resurrected rows. Settle one payout and insert its outbox event in a single transaction. Crash the dispatcher after publishing but before checkpointing; the consumer must produce one durable business effect for that event ID.</p>"
    "<pre><code class=\"language-text\">Data continuity acceptance gates\nSlot: restart position advances; retained WAL returns to budget\nCDC: source and sink IDs and sampled values reconcile\nOutbox: one transition, one event identity, duplicate delivery safe\nIndex: valid catalog state and measured query improvement\nDDL: blocked migration fails inside lock budget\nVacuum: old transaction owner found and horizon advances\nArchive: detached partition restores and queries correctly\nPITR: target boundary and acknowledged effects reconciled</code></pre>"
    "<h2>Change and recover data safely</h2><p>On a realistic table copy, build a customer-history index concurrently outside a transaction block and check its catalog validity. Hold a conflicting transaction open, run a nullable-column migration under a short session-local lock budget, and show it fails promptly. Resolve the blocker through its owner, then complete the compatible migration. Generate old row versions and demonstrate how an idle transaction affects cleanup. Detach a disposable old partition, restore its archive in another database, and only then mark it eligible for deletion. Finally inject an incorrect bulk update, recover a fresh instance to the chosen marker, and compare records immediately before and after the target. Fence the original writer and reconcile any externally acknowledged payouts after that marker.</p>"
    "<h2>Cost and verification</h2><p>Record disk growth, additional WAL and archive storage, connector replay time, index-build I/O, migration lock wait, and measured restore time. The drill passes only when a synthetic payout can be read from the recovered application path, no business effect was duplicated, and the last proven recovery point is stated precisely. A running database process or an advancing connector offset is insufficient evidence. Remove the isolated resources after the evidence is retained.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not drop a lagging slot without an offset recovery decision.</li><li>Do not run a concurrent index build inside a migration transaction.</li><li>Do not accept a PITR target before reconciling external effects.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub]))
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Data continuity recovery drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What does a lagging replication slot retain?", ["WAL still needed from its restart position", "Only a cached SQL query plan", "Only the newest image tag"], "The slot can hold log files while its consumer is offline."),
    ("What must precede dropping a stale slot?", ["Identify consumer, offset, and replay or resnapshot plan", "Delete all backups", "Increase worker replicas without checking disk"], "Dropping it can remove the only remaining change history."),
    ("How should a snapshot enter CDC streaming?", ["From a connector-supported source log position with sink deduplication", "From an estimated wall-clock minute", "From the first event after the next deployment"], "The handoff must cover concurrent changes without gaps."),
    ("What failure does a transactional outbox close?", ["Business state commits while event intent is missing", "Every consumer duplicate", "All network partitions"], "Business state and event intent share a database transaction."),
    ("Why can an outbox consumer still see a duplicate event?", ["Dispatcher may publish then crash before checkpoint", "The SQL transaction never commits", "The event ID changes the table schema"], "Publication and checkpoint are separate effects."),
    ("What must be checked after a concurrent index build?", ["Catalog validity and workload impact", "Only its name exists", "Only the database port is open"], "A failed concurrent build can leave an invalid index."),
    ("Where may CREATE INDEX CONCURRENTLY run?", ["As its own statement outside a transaction block", "Inside a migration transaction only", "Only after stopping all writes"], "PostgreSQL disallows that form inside a transaction block."),
    ("Why set a short lock_timeout for DDL?", ["Prevent a waiting schema change from queuing user work for too long", "Guarantee the schema change has no locks", "Make every table immutable"], "A bounded wait lets the migration fail before it blocks traffic."),
    ("What can hold old row versions alive despite autovacuum activity?", ["A long open transaction or retained replication horizon", "A newer image digest", "An unused DNS record"], "Cleanup must preserve versions still visible to old snapshots."),
    ("What does detaching a partition fail to do?", ["Free its storage and prove its archive is restorable", "Remove it from parent routing", "Leave it addressable as a separate table"], "Detach is a routing and metadata step, not final deletion."),
    ("What distinguishes a successful PITR from a database that merely starts?", ["Target-boundary checks and reconciliation of acknowledged effects", "A green process status alone", "A new timeline ID alone"], "Business records around the target must match the intended recovery point."),
    ("What must be fenced before recovered data accepts writes?", ["The original writer", "The read-only backup archive", "The SQL query planner"], "Two active writers can create divergent histories."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on WAL, CDC, outbox delivery, online DDL, retention, and PITR.",
            sort_order=19900, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the database operation that preserves a proven change history and a usable recovery point. A running process or completed job is only one piece of evidence.</p><h2>Review these lessons</h2>" + links(project_related) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-artifact-trust-decisions", "quizzes/devops-cluster-control-failures"]) + "<h3>Common Mistakes</h3><ul><li>Do not equate connector activity with sink correctness.</li><li>Do not call a restored server accepted before business reconciliation.</li></ul>"
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Data continuity check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/replica-lag-read-contract": ["devops/replication-slot-wal-budget"],
    "devops/event-schema-evolution": ["devops/cdc-snapshot-stream-handoff"],
    "devops/queue-consumer-reliability": ["devops/transactional-outbox-delivery"],
    "devops/database-change-safety": ["devops/concurrent-index-build-check", "devops/ddl-lock-budget"],
    "devops/database-pool-pressure": ["devops/vacuum-horizon-pressure"],
    "devops/immutable-backup-retention": ["devops/partition-retention-handoff"],
    "devops/backup-and-recovery": ["devops/pitr-timeline-acceptance"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))

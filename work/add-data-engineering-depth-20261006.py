"""Add original storage and operations modules to the Data Engineering curriculum."""

import datetime
import html
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
HUB = "data-engineering/data-engineering-tutorial"
PROJECT_HUB = HUB + "/project"
lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    lessons.append(dict(path="data-engineering/" + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add("schema-compatibility-and-consumer-rollout", "Schema compatibility and consumer rollout",
    "A schema contract defines how producers encode records and which historical and future records each consumer can read.", [
    ("Separate wire compatibility from meaning", "Adding a nullable field can be harmless for a decoder yet still break a downstream calculation that assumes the field is always present. Renaming an amount field while keeping its numeric type may preserve bytes but change business meaning. Record field identity, units, null behavior, keys, and deletion meaning in the contract. [[data-engineering/source-contract-and-raw-landing|Raw landing]] should retain the original payload and its schema version so a corrected parser can replay it."),
    ("Choose the reader and writer order", "Backward compatibility asks whether a new reader can consume older records; forward compatibility asks whether an older reader can consume records from a new writer. A rollout with persistent historical files needs a reader that understands old versions. A mixed fleet of consumers may also need old readers to understand new writes. Check the chosen compatibility rule against every supported version when old files or clients can survive more than one release."),
    ("Exercise an actual consumer fixture", "A registry check cannot test that a billing report still interprets cents as cents. Keep representative payloads from each supported version, including nulls, deleted entities, and unexpected enum values. Decode them with the candidate consumer, validate the resulting normalized record, then run the aggregate that matters. A failing contract test should block publication before [[data-engineering/quality-quarantine-and-reconciliation|quality gates]] see the changed data."),
    ("Publish in stages", "First deploy consumers that accept both old and new payloads. Then permit producers to emit the new version and monitor decode errors and unknown-field counts. Only retire old parsing after the retention horizon and dependent consumers have moved. A breaking change belongs in a new stream or versioned dataset with an explicit migration, not an unannounced reinterpretation of the existing one."),
    ("Make failure reversible", "Keep the last known-good schema and a rollback switch for the writer. Rolling back the binary alone does not remove records already emitted in the new format. If a new writer emitted 47 incompatible records, quarantine those records by event ID, repair or translate them, and replay from the raw log with the same deduplication key.")],
    '''SUPPORTED = {2: {"order_id", "amount_cents"},
             3: {"order_id", "amount_cents", "currency"}}

def normalize_order(payload, schema_version):
    if schema_version not in SUPPORTED:
        raise ValueError("unsupported order schema")
    if not SUPPORTED[schema_version].issubset(payload):
        raise ValueError("missing required field")
    if not isinstance(payload["amount_cents"], int):
        raise TypeError("amount must be integer cents")
    return {"order_id": payload["order_id"],
            "amount_cents": payload["amount_cents"],
            "currency": payload.get("currency", "INR")}

assert normalize_order({"order_id": "ord-47", "amount_cents": 7350}, 2)["currency"] == "INR"''',
    "A fixture suite is O(V × R) over V supported schema versions and R representative records. Real cost comes from keeping old readers and migration paths until retention ends. A registry compatibility result is necessary for encoded records, but semantic checks and staged rollout still need their own tests.",
    ["Do not assume an optional wire field is optional in every consumer calculation.", "Do not equate an accepted schema change with a safe unit or enum change.", "Do not remove a reader for old data while retained files still use it."],
    ["data-engineering/source-contract-and-raw-landing", "data-engineering/quality-quarantine-and-reconciliation", "data-engineering/parquet-row-groups-and-column-pruning", "data-engineering/lakehouse-snapshot-and-atomic-commit", "data-engineering/versioned-order-lake-release-project", "data-engineering/dag-intervals-and-idempotent-tasks"], "Storage contracts and table design")

add("parquet-row-groups-and-column-pruning", "Parquet row groups, projection and scan cost",
    "Parquet groups rows into row groups and stores each column's values together, so a query can skip unneeded columns and sometimes whole row groups.", [
    ("Connect layout to a query", "An order analyst selecting order ID, status, and amount from a 63-column table should not scan every column chunk. Column projection avoids irrelevant bytes. If a row group has useful min and max statistics for event date, a date filter may skip that group; the engine must still read a group whose range overlaps the filter. Statistics are an optimization, not a correctness filter."),
    ("Distinguish file from table", "A Parquet file contains data and footer metadata. It does not, by itself, supply a multi-file transaction, snapshot isolation, or a reliable table-wide deletion protocol. Use a table format or a controlled manifest when readers need a consistent set of files. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Snapshot publication]] makes that distinction concrete."),
    ("Plan row groups and files together", "A very small row group has high metadata overhead and weak scan amortization. A huge row group may waste reads when predicates are selective and can limit parallel work. Many tiny files increase listing, open, planning, and task-launch costs even if the compressed bytes are few. Choose sizes from representative queries and measured storage behavior rather than one universal target."),
    ("Sort for the filters that matter", "Grouping nearby event dates can make row-group ranges tighter and improve skipping for time-bounded queries. Sorting on every candidate column is impossible; it adds write work and may help one query while hurting another. Compare bytes scanned, files opened, and elapsed time before and after a layout change. [[data-engineering/partition-planning-and-skew|Partition design]] determines a coarser pruning boundary."),
    ("Watch evolving schemas", "Files written under several schemas can coexist. Readers must resolve missing columns, field types, and defaults consistently across them. A read that silently converts missing amount to zero can create false revenue. [[data-engineering/schema-compatibility-and-consumer-rollout|The schema contract]] should state whether the field is absent, null, or truly zero.")],
    '''row_group_stats = [
    {"file": "orders-a", "min_day": 40, "max_day": 46, "bytes": 120_000},
    {"file": "orders-b", "min_day": 47, "max_day": 53, "bytes": 145_000},
    {"file": "orders-c", "min_day": 54, "max_day": 60, "bytes": 132_000},
]

def candidate_groups(groups, first_day, last_day):
    return [group for group in groups
            if group["max_day"] >= first_day and group["min_day"] <= last_day]

scan = candidate_groups(row_group_stats, 48, 50)
assert [group["file"] for group in scan] == ["orders-b"]
assert sum(group["bytes"] for group in scan) == 145_000''',
    "Planning from G row-group statistics takes O(G) work in this example; a table catalog may prune earlier. Projection reduces bytes for unused columns, while row-group skipping reduces candidate groups. Neither eliminates a costly join or an incorrect table grain.",
    ["Do not call a Parquet file an ACID table.", "Do not expect min/max skipping when ranges overlap widely or statistics are absent.", "Do not optimize compressed bytes alone while file-open overhead dominates."],
    ["data-engineering/partition-planning-and-skew", "data-engineering/lakehouse-snapshot-and-atomic-commit", "data-engineering/compaction-retention-and-replay-horizon", "data-engineering/schema-compatibility-and-consumer-rollout", "data-engineering/versioned-order-lake-release-project"], "Storage contracts and table design")

add("partition-planning-and-skew", "Partition planning, pruning and skew",
    "A partition spec groups rows by a transform so readers can skip unrelated files; its value depends on query predicates and the distribution of rows.", [
    ("Start with the dominant read", "A support dashboard usually filters orders by event day and sometimes region. Day partitions can bound the files considered for a seven-day report. Partitioning by individual order ID would create nearly one partition per order, making metadata and file counts unmanageable. A partition key must reduce scans without exploding the number of small groups."),
    ("Use event time deliberately", "Landing date and business event date are different. Late events received today may belong to an event-day partition from last month. If consumers ask for historical order date, partition on that date and include old partitions in the correction plan. [[data-engineering/event-time-and-late-arrivals|Late-arrival policy]] should define how long the system rewrites earlier partitions."),
    ("Inspect skew before scaling", "A region named 'unknown' may contain 68% of all orders. Giving it one processing task while smaller regions each get one task leaves most workers idle. Calculate counts and bytes by partition and by join key. Salted keys, repartitioning, or a separate heavy-key path may help; each changes shuffle cost and must preserve the output key and count."),
    ("Keep partition evolution readable", "A table can move from day partitions to month plus bucket partitions as data and access patterns change. Readers must still find older data laid out under the earlier spec. A transaction-aware table catalog can track which spec produced each file. Without one, a migration needs a versioned manifest and a read path aware of both layouts. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Snapshot commits]] isolate the switch."),
    ("Measure the trade", "Compare the fraction of files pruned for real queries, total files, worst partition size, write amplification from corrections, and p95 query latency. A spec that reduces a full scan but creates 190,000 tiny files may be a net loss. [[data-engineering/compaction-retention-and-replay-horizon|Compaction]] can reduce file count, but cannot fix a partition key that does not match filters.")],
    '''from collections import Counter

orders = [
    {"day": 47, "region": "north"}, {"day": 47, "region": "unknown"},
    {"day": 47, "region": "unknown"}, {"day": 48, "region": "south"},
    {"day": 49, "region": "unknown"},
]

def partition_counts(records):
    counts = Counter((record["day"], record["region"]) for record in records)
    return dict(counts)

counts = partition_counts(orders)
assert counts[(47, "unknown")] == 2
assert sum(counts.values()) == len(orders)''',
    "Counting N rows is O(N) time and O(P) memory for P observed partitions. A finer partition spec can reduce read bytes but raises metadata, file-opening, and correction costs. Benchmark the full workload rather than a single selective query.",
    ["Do not partition by a near-unique identifier.", "Do not use ingest day when users filter by event day without accounting for late data.", "Do not report only average partition size when one key dominates."],
    ["data-engineering/parquet-row-groups-and-column-pruning", "data-engineering/event-time-and-late-arrivals", "data-engineering/lakehouse-snapshot-and-atomic-commit", "data-engineering/compaction-retention-and-replay-horizon", "data-engineering/versioned-order-lake-release-project"], "Storage contracts and table design")

add("lakehouse-snapshot-and-atomic-commit", "Table snapshots and atomic publication",
    "A table snapshot names one committed set of data and delete files, letting readers observe a complete version while writers prepare the next.", [
    ("Treat files as candidates until commit", "An order correction may write three new files and retire two old ones. If a reader lists the directory halfway through, it can combine incompatible generations. Instead, write immutable candidate files, validate their row counts and checksums, then commit a new metadata pointer that names exactly the accepted files. [[data-engineering/backfill-publication-boundary|Backfill publication]] follows the same boundary."),
    ("Understand conflict detection", "Two writers can start from snapshot 41 and both prepare updates. A commit protocol must validate whether either writer changed data that the other relied on, then reject or retry a conflicting commit. Blindly replacing the pointer with the last writer's manifest loses earlier work. A retry must recalculate against the current snapshot rather than reuse an invalid old read set."),
    ("Keep reads pinned", "A report that reads several files should pin a snapshot ID for its whole job. It must not fetch the newest pointer between partitions. Record the snapshot ID with the report and its query version so a later discrepancy can be reproduced. [[data-science/reproducible-analysis-snapshot|Analysis snapshots]] extend this discipline to code and cutoff time."),
    ("Account for row-level changes", "Some table formats represent deletes separately from data files. The reader must apply all delete files valid for its snapshot; a raw Parquet reader that ignores them can expose deleted rows. Deletion file format and applicability vary by table specification, so test through the production engine before claiming the row is gone. [[data-engineering/deletion-propagation-and-erasure-proof|Erasure verification]] must check every reader path."),
    ("Publish only after checks", "For a daily order table, compare source count, accepted count, quarantined count, and distinct order keys before commit. If 47 source records become 45 accepted plus two quarantined, that balance is coherent; 44 plus two is not. A failed validation should leave the previous snapshot visible and the candidate files eligible for safe cleanup.")],
    '''snapshots = {41: {"orders-a", "orders-b"}}

def commit_snapshot(history, expected_parent, add_files, remove_files):
    current = max(history)
    if current != expected_parent:
        raise RuntimeError("stale parent snapshot")
    old_files = history[current]
    if not set(remove_files).issubset(old_files):
        raise ValueError("remove set not in parent")
    next_id = current + 1
    history[next_id] = (old_files - set(remove_files)) | set(add_files)
    return next_id

assert commit_snapshot(snapshots, 41, {"orders-c"}, {"orders-a"}) == 42
assert snapshots[41] == {"orders-a", "orders-b"}
assert snapshots[42] == {"orders-b", "orders-c"}''',
    "The set operation shown costs O(F) time and space for F files in the parent manifest. Real table formats use metadata trees and optimistic commits to avoid copying every file name for every write. Snapshot metadata, conflict retries, and old-file retention add cost in exchange for consistent reads.",
    ["Do not expose candidate files through directory listing before commit.", "Do not retry a conflicting write without rechecking its read set.", "Do not read raw data files while ignoring snapshot-specific deletes."],
    ["data-engineering/backfill-publication-boundary", "data-engineering/compaction-retention-and-replay-horizon", "data-engineering/deletion-propagation-and-erasure-proof", "data-engineering/partition-planning-and-skew", "data-engineering/versioned-order-lake-release-project", "data-science/reproducible-analysis-snapshot"], "Storage contracts and table design")

add("compaction-retention-and-replay-horizon", "Compaction, retention and the replay horizon",
    "Compaction rewrites small or fragmented files into fewer files; retention decides when old snapshots and their unreferenced files may be removed.", [
    ("Name the reason to compact", "A stream writing 2,400 five-kilobyte files per hour can spend more time opening files than scanning rows. Bin-packing them into larger files lowers open and planning overhead. It does not reduce the logical row count or repair duplicate records. Measure file count, average compressed size, query planning time, and bytes rewritten before scheduling the job."),
    ("Separate a rewrite from publication", "A compactor writes replacement files, validates row totals and key-level checksums, and commits a new snapshot that swaps file references. Readers pinned to the older snapshot keep seeing the old files. A failed rewrite must leave old references intact. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Snapshot commits]] provide this isolation; deleting files as soon as the replacement is written does not."),
    ("Set retention from real dependencies", "A month-end audit may need a snapshot from 35 days ago even when routine dashboards need only a week. A delayed CDC replay may need source logs, original raw records, schemas, and the table snapshot that formed its input. List each recovery and audit requirement, then set retention to the longest required horizon plus operational margin. [[data-engineering/cdc-replay-and-deletes|CDC replay]] fails if its earliest necessary source position has expired."),
    ("Prove cleanup safety", "Old snapshots can reference files still needed by pinned readers, rollback plans, or branches. First expire eligible references according to the table's retention rules; then remove only orphan files that no live reference can reach, after a delay that covers in-flight writes. Keep a dry-run manifest and deletion count. Mistaking a candidate write for an orphan is a data-loss event."),
    ("Watch write amplification", "Compacting every partition on every ingest batch repeatedly rewrites the same bytes. Target partitions whose file count or average size crosses a measured threshold. A hot partition may need scheduled compaction after its late-arrival window closes. [[data-engineering/partition-planning-and-skew|Skew diagnostics]] identify partitions that deserve separate treatment.")],
    '''files = [
    {"name": "day47-a", "day": 47, "bytes": 28_000},
    {"name": "day47-b", "day": 47, "bytes": 34_000},
    {"name": "day48-a", "day": 48, "bytes": 156_000},
]

def compaction_candidates(manifest, min_file_bytes=50_000):
    by_day = {}
    for item in manifest:
        if item["bytes"] < min_file_bytes:
            by_day.setdefault(item["day"], []).append(item["name"])
    return {day: names for day, names in by_day.items() if len(names) > 1}

assert compaction_candidates(files) == {47: ["day47-a", "day47-b"]}''',
    "Scanning F file summaries is O(F) time and O(P + C) memory for P candidate partitions and C candidate files. A real rewrite costs read and write I/O for every selected byte. Excessive compaction trades query savings for higher storage and compute bills.",
    ["Do not delete old files before all retained snapshots stop referring to them.", "Do not compact on a timer without checking file sizes and write amplification.", "Do not set retention shorter than replay, audit, or rollback requirements."],
    ["data-engineering/parquet-row-groups-and-column-pruning", "data-engineering/lakehouse-snapshot-and-atomic-commit", "data-engineering/partition-planning-and-skew", "data-engineering/deletion-propagation-and-erasure-proof", "data-engineering/versioned-order-lake-release-project", "data-engineering/cdc-replay-and-deletes"], "Storage contracts and table design")

add("deletion-propagation-and-erasure-proof", "Deletion propagation and erasure proof",
    "A deletion request is complete only when every authorized serving path stops returning the subject and the remaining retained copies follow a defined erasure schedule.", [
    ("Inventory the copies", "One customer identifier may appear in a raw event log, current customer table, warehouse history, feature snapshot, search index, export, and backup. Deleting only the primary table leaves other paths readable. Maintain a dataset inventory with owner, purpose, key format, retention, deletion method, and verification query. [[data-engineering/pipeline-lineage-and-impact-analysis|Lineage]] helps find descendants, but untracked manual exports need a separate inventory."),
    ("Distinguish logical and physical removal", "A table delete may mark rows invisible in the current snapshot while their bytes remain in old files or snapshots until rewrite and retention cleanup. That can satisfy an immediate serving requirement, but physical erasure requires additional work. Define which guarantees apply to live queries, time travel, raw storage, caches, and backups; do not treat one SQL DELETE as proof for all of them."),
    ("Track an erasure job", "Assign a request ID and normalized subject key, then record every target dataset, attempted operation, completion state, and evidence timestamp. Deduplicate repeated requests. A transient failure in one downstream index should remain visible and retryable, while already completed targets should not be reinserted from an old backfill. [[data-engineering/backfill-publication-boundary|Backfill publication]] must consult the active deletion ledger."),
    ("Verify through production readers", "Run the same queries and API reads that users and internal jobs use, pinned to the post-delete snapshot where applicable. Check the current table, historical views, and downstream serving stores. A count of zero in one warehouse table is insufficient if a cached endpoint still returns the customer. For backups that cannot be modified in place, record expiry and require reapplication of the ledger during restore."),
    ("Prevent reappearance", "Keep tombstones or a suppression ledger long enough that delayed CDC, retries, and raw replay cannot recreate the subject. Treat a create event older than the deletion boundary as stale. If the business legitimately creates a new account with the same identifier, define a new entity epoch; otherwise key reuse can make the suppression rule ambiguous.")],
    '''deletion_ledger = {"cust-47": 131}
events = [
    {"customer": "cust-47", "source_position": 128, "kind": "upsert"},
    {"customer": "cust-83", "source_position": 129, "kind": "upsert"},
]

def publishable_events(records, tombstones):
    return [record for record in records
            if record["customer"] not in tombstones]

assert [record["customer"] for record in publishable_events(events, deletion_ledger)] == ["cust-83"]''',
    "Filtering N events against a hashed ledger is O(N) expected time and O(N) output space; ledger storage grows with active suppression keys. Full physical erasure can require rewriting files and waiting through backup retention. The code demonstrates a replay barrier, not a substitute for authorization or legal retention policy.",
    ["Do not call a logical table delete physical erasure.", "Do not let backfills ignore the deletion ledger.", "Do not claim completion from one table query when caches or exports remain."],
    ["data-engineering/cdc-replay-and-deletes", "data-engineering/lakehouse-snapshot-and-atomic-commit", "data-engineering/compaction-retention-and-replay-horizon", "data-engineering/pipeline-lineage-and-impact-analysis", "data-engineering/versioned-order-lake-release-project", "privacy-aware-ml/privacy-aware-ml-tutorial"], "Storage contracts and table design")

add("versioned-order-lake-release-project", "Project: release a versioned order lake",
    "Build a versioned order table that accepts two payload schemas, prunes useful partitions, commits complete snapshots, and proves a deletion survives replay.", [
    ("Fix the release contract", "The source produces order events with order ID, amount in integer cents, event day, and a schema version. Version three adds currency, while version two defaults to INR. Define one current row per order ID, ordered by source position; a delete event removes that row. Keep a raw immutable batch and a rejected-record ledger so the accepted plus rejected count matches the source count."),
    ("Build two candidate partitions", "Prepare day 47 and day 48 output under new file names. A late correction to an order from day 47 must rewrite or merge into that event-day partition even if it arrives on day 52. Record file sizes, min/max days, distinct keys and a checksum before commit. [[data-engineering/partition-planning-and-skew|Partition design]] should make the day-bounded audit scan cheaper without creating one file per order."),
    ("Simulate a failed commit", "Start from snapshot 41. Have writer A prepare a corrected order and writer B prepare a deletion against the same parent. Commit B first. Writer A must receive a stale-parent error, reload snapshot 42, apply the tombstone, and rebuild its candidate. Publishing A's old candidate would resurrect the deleted order. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Atomic publication]] supplies the conflict boundary."),
    ("Run release checks", "Decode retained version-two and version-three fixtures, check the amount unit, verify accepted plus quarantined equals extracted, and query the table through a pinned snapshot. Execute a deletion request and replay the old raw batch; the subject must stay absent. Inspect one audit query's candidate row groups and compare bytes scanned to a full scan. Record the exact snapshot ID and schema versions in the release packet."),
    ("State the outcome and rollback", "Ship only when both schema fixtures decode, checksums match, the conflict test rejects stale publication, and deletion verification passes. A rollback points readers to the previous allowed snapshot only if doing so cannot expose a subject that must remain erased; otherwise repair forward. Record what evidence is still pending when backup expiry extends beyond the release window.")],
    '''source_events = [
    {"order_id": "ord-47", "position": 81, "kind": "upsert", "amount_cents": 7350},
    {"order_id": "ord-83", "position": 82, "kind": "upsert", "amount_cents": 4200},
    {"order_id": "ord-47", "position": 84, "kind": "delete"},
]

def materialize_current(records):
    current = {}
    for event in sorted(records, key=lambda item: item["position"]):
        if event["kind"] == "delete":
            current.pop(event["order_id"], None)
        else:
            current[event["order_id"]] = event["amount_cents"]
    return current

assert materialize_current(source_events) == {"ord-83": 4200}''',
    "Sorting N events costs O(N log N) time and O(N) space; an already ordered change log can be applied in O(N) time. File rewrite and validation cost depend on affected partitions, not only changed rows. The release packet must also price retained snapshots and the deletion ledger.",
    ["Do not merge rows by arrival time when source position defines order.", "Do not publish a stale candidate after a concurrent deletion.", "Do not roll back to a snapshot that would expose an erased subject."],
    ["data-engineering/schema-compatibility-and-consumer-rollout", "data-engineering/parquet-row-groups-and-column-pruning", "data-engineering/partition-planning-and-skew", "data-engineering/lakehouse-snapshot-and-atomic-commit", "data-engineering/compaction-retention-and-replay-horizon", "data-engineering/deletion-propagation-and-erasure-proof", "data-engineering/receipt-pipeline-replay-project"], "Storage contracts and table design", True)

add("dag-intervals-and-idempotent-tasks", "DAG intervals and idempotent task outputs",
    "A pipeline DAG declares dependencies among bounded tasks; each run must identify the exact input interval and produce the same committed result on retry.", [
    ("Use interval identity, not wall-clock now", "A daily billing task for event day 47 should read the declared day-47 source snapshot even when it is retried on day 52. Calling the current time inside the transformation changes its input and makes the retry a different calculation. Put interval start, interval end, input snapshot IDs and code version in the run context. [[data-engineering/replay-manifest-and-audit-trail|A replay manifest]] makes those choices inspectable."),
    ("Give each task a publication boundary", "A task may build a candidate output in temporary storage, but downstream tasks should consume only a validated committed artifact. Writing 70% of a partition and then failing must not leave a visible partial table. An upsert keyed by grain or an atomic partition replacement can make a retry converge. An append without a duplicate key usually cannot. [[data-engineering/idempotent-load-and-checkpoint|Idempotent loads]] cover the database side of this rule."),
    ("Model dependencies at the data level", "A transform should wait for the source interval and its quality checks, not merely for a clock tick. If source A is ready and source B is delayed, do not build a silently partial join. Mark the run blocked with the missing dataset and cutoff. [[data-engineering/dependency-readiness-and-source-freshness|Readiness checks]] distinguish absent data from empty but complete data."),
    ("Bound parallelism", "A backfill of 240 daily intervals can overwhelm the warehouse if every interval starts at once. Limit active runs and expensive tasks, then prioritize recent consumer-critical intervals if that matches the recovery policy. Keep each interval independently rerunnable, but document dependencies when a cumulative model needs sequential checkpoints."),
    ("Test retry equivalence", "Run the same interval twice from the same pinned inputs. Compare output row count, keys and a canonical checksum; the second run must not add duplicate bills or change amounts. Then inject a failure after writing candidate data and verify the published table still points to the previous complete result.")],
    '''from hashlib import sha256

def run_key(pipeline, interval_start, interval_end, input_snapshot):
    identity = f"{pipeline}|{interval_start}|{interval_end}|{input_snapshot}"
    return sha256(identity.encode()).hexdigest()[:16]

first = run_key("daily-billing", 47, 48, "snap-41")
retry = run_key("daily-billing", 47, 48, "snap-41")
different_input = run_key("daily-billing", 47, 48, "snap-42")
assert first == retry
assert first != different_input''',
    "Run-key calculation is O(L) in the identity length. The expensive part is staging, validating, and publishing each interval. More parallel tasks reduce elapsed time until warehouse slots, source rate limits, or commit conflicts become the bottleneck.",
    ["Do not use the retry time as the event interval.", "Do not let a failed task expose a partial partition.", "Do not equate a scheduler success state with validated downstream data."],
    ["data-engineering/idempotent-load-and-checkpoint", "data-engineering/dependency-readiness-and-source-freshness", "data-engineering/failure-classification-and-retry-budget", "data-engineering/replay-manifest-and-audit-trail", "data-engineering/billing-pipeline-operations-project", "data-engineering/backfill-publication-boundary"], "Orchestration and production operations")

add("dependency-readiness-and-source-freshness", "Dependency readiness and source freshness",
    "A source is ready for a pipeline interval when its declared completeness condition is met; freshness says how far the observed data trails the expected event or ingest clock.", [
    ("Do not confuse present with complete", "A day-47 object may exist while its uploader has sent only 60% of the batch. An empty interval may be valid if the producer explicitly marks it complete. Prefer a producer manifest containing interval, expected files or count, checksum and completion timestamp. A polling task should wait for the manifest and verify it, not just test for one file path."),
    ("Choose the clock", "Ingest freshness measures when the platform last received data; event freshness measures when the newest business event occurred. A source with frequent retries can appear ingest-fresh while its latest business event is days old. Record both timestamps and the expected cadence. [[data-engineering/event-time-and-late-arrivals|Late-event policy]] states whether an interval may receive corrections after initial completion."),
    ("Set a useful threshold", "If a dispatch dashboard is promised by 08:30, a source arriving at 08:24 leaves six minutes for transformation and validation. A readiness threshold of 08:29 is too late. Work backward from consumer deadline, p95 processing time, and an operational margin. Alert on a missed readiness boundary before the dashboard itself is late."),
    ("Express blocked states", "A pipeline waiting on a late source is blocked, not failed by its own computation. Record the missing interval, producer owner, last observed event time and deadline. Retry checks at a bounded rate. When the source completes, run against its pinned version; if it misses the cutoff, follow a documented stale-data or no-publish policy rather than silently reusing yesterday's data."),
    ("Keep readiness separate from quality", "A completed batch of 2,700 records may still contain impossible amounts or duplicate keys. Completeness proves that extraction finished; [[data-engineering/quality-quarantine-and-reconciliation|quality gates]] decide whether the records are publishable. Both statuses must appear in the release manifest.")],
    '''source_manifest = {"interval": 47, "expected_files": 3,
                   "observed_files": 3, "complete": True,
                   "latest_event_minute": 474}

def source_status(manifest, required_interval, newest_allowed_minute):
    if manifest["interval"] != required_interval:
        return "wrong_interval"
    if not manifest["complete"] or manifest["observed_files"] != manifest["expected_files"]:
        return "incomplete"
    if manifest["latest_event_minute"] < newest_allowed_minute:
        return "stale"
    return "ready"

assert source_status(source_manifest, 47, 470) == "ready"
assert source_status(source_manifest, 47, 480) == "stale"''',
    "A manifest check is O(1) for fixed summary fields, plus O(F) to verify F file checksums when required. Polling too often raises storage or API cost without making an unavailable source arrive sooner. Set cadence from the deadline and source behavior.",
    ["Do not use file existence as proof of complete delivery.", "Do not measure only ingest freshness when business events can stall.", "Do not publish stale data without labeling the cutoff and consumer policy."],
    ["data-engineering/dag-intervals-and-idempotent-tasks", "data-engineering/quality-quarantine-and-reconciliation", "data-engineering/pipeline-slos-and-error-budgets", "data-engineering/replay-manifest-and-audit-trail", "data-engineering/billing-pipeline-operations-project", "data-engineering/event-time-and-late-arrivals"], "Orchestration and production operations")

add("pipeline-lineage-and-impact-analysis", "Pipeline lineage and impact analysis",
    "Lineage records which input datasets and transformations produced an output, allowing a changed source or failed run to be traced to affected consumers.", [
    ("Record concrete dataset identities", "A name such as orders is ambiguous across environments, regions and snapshots. Use a namespace, dataset name, version or snapshot ID, and run ID. Record input and output versions at completion, even when a job declares its expected dependencies in code. [[data-engineering/replay-manifest-and-audit-trail|The run manifest]] links observed lineage to the exact published artifact."),
    ("Avoid false edges", "A job may read customers and orders but independently write a customer count and an order total. Treating every input as a source of every output invents dependencies that do not exist. Capture edges at the transformation or output-field level when impact decisions require that precision. A coarse DAG remains useful for initial discovery, but it should not claim exact column provenance."),
    ("Use lineage to plan a change", "Before changing amount_cents to a new currency unit, traverse descendants to find reports, features, exports and caches. For each consumer, identify owner, compatibility requirement, test fixture and rollout order. [[data-engineering/schema-compatibility-and-consumer-rollout|Schema rollout]] needs this dependency list. The existence of a lineage edge alone does not prove the consumer can decode or interpret the change."),
    ("Use lineage during an incident", "If an incorrect exchange-rate table was published at 06:10, find runs that consumed that version and outputs they published. Mark those outputs suspect, pause their downstream publication, repair the source, and replay affected intervals. A broad table-level edge may overstate the blast radius; that's safer than missing a real descendant, but costs more recovery work."),
    ("Keep manual data flows visible", "Not every export, notebook or one-off upload emits metadata events. Maintain a register for critical manual transfers and periodically compare read logs to the catalog. A lineage graph can be technically correct for observed jobs yet incomplete for the business. [[data-engineering/deletion-propagation-and-erasure-proof|Deletion work]] cannot rely only on instrumented edges.")],
    '''from collections import deque

downstream = {
    "raw.orders": {"curated.orders", "audit.order_events"},
    "curated.orders": {"finance.daily_revenue", "ml.order_features"},
    "audit.order_events": set(),
    "finance.daily_revenue": set(),
    "ml.order_features": set(),
}

def affected_datasets(graph, changed):
    seen, pending = set(), deque([changed])
    while pending:
        dataset = pending.popleft()
        for child in graph.get(dataset, ()):
            if child not in seen:
                seen.add(child)
                pending.append(child)
    return seen

assert "finance.daily_revenue" in affected_datasets(downstream, "raw.orders")''',
    "A breadth-first traversal is O(V + E) over V datasets and E dependency edges, with O(V) memory. Producing and retaining accurate run-level lineage costs instrumentation and catalog storage. Missing edges are a bigger risk than traversal speed.",
    ["Do not infer every input feeds every output in a multi-output job.", "Do not use a dataset name without environment and version identity.", "Do not assume an instrumented graph includes manual exports."],
    ["data-engineering/schema-compatibility-and-consumer-rollout", "data-engineering/replay-manifest-and-audit-trail", "data-engineering/deletion-propagation-and-erasure-proof", "data-engineering/pipeline-slos-and-error-budgets", "data-engineering/billing-pipeline-operations-project", "knowledge-graphs/knowledge-graphs-tutorial"], "Orchestration and production operations")

add("pipeline-slos-and-error-budgets", "Pipeline SLOs, freshness and error budgets",
    "A pipeline service-level objective states the measurable share of intervals whose usable data arrives before a consumer deadline with the required quality.", [
    ("Define a good interval", "For the finance daily table, define success as a committed day partition by 08:30 local time, all required source manifests complete, accepted plus quarantined count equal to extracted count, and no critical quality violation. A scheduler's green task status is not enough. The user-facing unit is a usable interval, so measure it from the consumer's query path."),
    ("Calculate the budget", "An objective of 99% good daily intervals over a 100-day rolling window permits one bad interval. A target of 99.9% on only 30 daily intervals is hard to interpret because one failure moves the observed rate by more than three percentage points. Select a window and unit with enough opportunities, or use a weekly or per-run target with clear meaning."),
    ("Separate symptoms", "Track source lag, processing duration, quality rejection rate and publication delay alongside the final good-interval indicator. A late source and a slow transform require different owners. [[data-engineering/dependency-readiness-and-source-freshness|Readiness]] tells whether the source delivered; [[data-engineering/failure-classification-and-retry-budget|failure classification]] tells whether retrying helps."),
    ("Alert for action", "Page a human when the consumer deadline is at risk and the team can act, not on every transient task retry. A warning can trigger at 07:50 when the source is missing; an incident can trigger at 08:30 when no valid snapshot is published. Include affected dataset, interval, run ID, last good snapshot and runbook path in the alert."),
    ("Use the budget in release decisions", "If recent intervals exhausted the failure budget, postpone a risky schema change and repair the unstable pipeline first. The budget is not a reason to hide bad intervals or lower quality gates. A data product with a strict deletion or financial correctness requirement may need a separate zero-tolerance guardrail even when its freshness objective permits rare lateness.")],
    '''daily_intervals = [
    {"day": 47, "ready": True, "quality_ok": True, "published_minute": 506},
    {"day": 48, "ready": True, "quality_ok": True, "published_minute": 518},
    {"day": 49, "ready": False, "quality_ok": False, "published_minute": None},
]

def good_interval_rate(records, deadline_minute=510):
    if not records:
        raise ValueError("no intervals")
    good = sum(record["ready"] and record["quality_ok"]
               and record["published_minute"] is not None
               and record["published_minute"] <= deadline_minute
               for record in records)
    return good / len(records)

assert good_interval_rate(daily_intervals) == 1 / 3''',
    "Aggregating N intervals is O(N) time and O(1) extra space. Monitoring cost comes from trustworthy source and publication timestamps, retention of interval outcomes, and alerts with enough context to act. A small denominator can make percentage targets misleading.",
    ["Do not measure only task success when the published table is unusable.", "Do not set an SLO without a consumer deadline and quality condition.", "Do not treat a freshness allowance as permission to publish wrong financial data."],
    ["data-engineering/dependency-readiness-and-source-freshness", "data-engineering/failure-classification-and-retry-budget", "data-engineering/pipeline-lineage-and-impact-analysis", "data-engineering/replay-manifest-and-audit-trail", "data-engineering/billing-pipeline-operations-project", "data-engineering/quality-quarantine-and-reconciliation"], "Orchestration and production operations")

add("failure-classification-and-retry-budget", "Failure classification and retry budgets",
    "A retry policy repeats only failures likely to clear without changing the data or code, while limiting attempts so an outage cannot flood an upstream system.", [
    ("Classify before repeating", "A connection reset or temporary rate limit may clear. A malformed schema, missing required field or violated uniqueness rule will fail again on the same input. Put those records in a quarantine path with context and stop the interval before publication. [[data-engineering/quality-quarantine-and-reconciliation|Quality gates]] handle data defects; retries handle transient execution defects."),
    ("Bound attempts and total delay", "Five rapid retries against an overloaded source can amplify its failure. Use a finite attempt count, exponential delay with jitter, a deadline tied to the consumer SLO, and a circuit breaker when the upstream dependency is broadly unavailable. The deadline matters: a retry after the finance cutoff may be useful for repair, but cannot make that interval on time."),
    ("Make side effects safe", "A task that posts a billing export can succeed remotely and lose its acknowledgement locally. Blind retry can send the export twice. Use a stable idempotency key understood by the receiver, or write to a staging resource and commit once. If the external endpoint cannot deduplicate, reconcile its state before repeating. [[data-engineering/dag-intervals-and-idempotent-tasks|Task interval identity]] supplies a stable key."),
    ("Separate pause from discard", "When a rate limit lasts longer than the retry budget, mark the interval blocked or failed with its exact input snapshot and resumable checkpoint. Do not skip source positions to keep a dashboard green. [[data-engineering/idempotent-load-and-checkpoint|Checkpoint discipline]] makes recovery possible after the dependency returns."),
    ("Exercise an uncertain outcome", "In a release test, simulate the receiver accepting a request while the client times out. Re-run with the same idempotency key and confirm there is one export. Also test a permanent schema error and confirm it is not retried. Record attempt count, last error class and next action in the run log so an operator does not infer state from silence.")],
    '''def retry_plan(error_kind, attempt, max_attempts=4):
    permanent = {"invalid_schema", "duplicate_business_key", "missing_field"}
    transient = {"timeout", "connection_reset", "rate_limited"}
    if error_kind in permanent:
        return {"action": "quarantine", "delay_seconds": 0}
    if error_kind not in transient or attempt >= max_attempts:
        return {"action": "stop", "delay_seconds": 0}
    return {"action": "retry", "delay_seconds": min(6 * (2 ** (attempt - 1)), 48)}

assert retry_plan("timeout", 2) == {"action": "retry", "delay_seconds": 12}
assert retry_plan("invalid_schema", 1)["action"] == "quarantine"
assert retry_plan("rate_limited", 4)["action"] == "stop"''',
    "A policy decision is O(1); each retry repeats the task's I/O and compute cost. This deterministic delay example omits jitter so its assertion is reproducible; production schedules should add bounded jitter and honor an upstream retry-after value when available.",
    ["Do not retry permanent data or schema errors.", "Do not assume a client timeout means the remote side did nothing.", "Do not use unbounded retries that outlive the consumer deadline."],
    ["data-engineering/dag-intervals-and-idempotent-tasks", "data-engineering/idempotent-load-and-checkpoint", "data-engineering/dependency-readiness-and-source-freshness", "data-engineering/pipeline-slos-and-error-budgets", "data-engineering/replay-manifest-and-audit-trail", "data-engineering/billing-pipeline-operations-project"], "Orchestration and production operations")

add("replay-manifest-and-audit-trail", "Replay manifests and audit trails",
    "A replay manifest pins the input positions, dataset versions, code version, interval and output identity needed to rerun or explain a pipeline result.", [
    ("Capture the actual inputs", "A day-47 billing run reads source snapshot 41, exchange-rate snapshot 12 and source positions 900 through 1,147. Record those identifiers at execution, not just the logical table names. If the upstream table changes next week, 'rerun day 47' without a pinned version does not reproduce the original result. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Snapshot identity]] anchors file-based tables."),
    ("Record transformation identity", "Store the code commit or artifact digest, configuration version, schema versions and execution parameters. Secrets do not belong in the manifest. A retry with the same manifest should produce the same canonical output checksum; a deliberate correction should create a new manifest and link to the superseded run."),
    ("Represent counts and decisions", "For each stage, record extracted, accepted, quarantined, deleted and published counts at a declared grain. A source count of 1,147 with 1,139 accepted, six quarantined and two deletion events can reconcile if those categories partition the source events; explain that arithmetic in the contract. [[data-engineering/quality-quarantine-and-reconciliation|Reconciliation]] should fail before publication when counts do not balance."),
    ("Tie manifests to lineage", "The manifest records a run's exact inputs and output. The lineage graph connects that output to later consumers. Together they answer which reports used a bad exchange-rate version and which input should be replayed. [[data-engineering/pipeline-lineage-and-impact-analysis|Impact analysis]] walks this graph, then the manifests select the precise intervals."),
    ("Protect the audit record", "Write manifests immutably or version them with a tamper-evident digest, restrict who can amend them, and retain them at least as long as their associated data and audit requirement. A manifest that names expired source data cannot guarantee replay; keep retention schedules aligned. Document a forward repair when exact replay is impossible, rather than calling a reconstruction identical.")],
    '''import hashlib
import json

run_manifest = {
    "interval": [47, 48], "source_snapshot": "snap-41",
    "rate_snapshot": "rates-12", "source_positions": [900, 1147],
    "code_digest": "billing-v3", "output_snapshot": "snap-42",
}

def manifest_digest(manifest):
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()

assert manifest_digest(run_manifest) == manifest_digest(dict(reversed(list(run_manifest.items()))))''',
    "Canonical serialization and hashing cost O(B) time and space for B manifest bytes. The larger operational cost is retaining addressable input versions and connecting manifests to published outputs. A digest detects change; it does not prove the source data was truthful.",
    ["Do not store only table names when exact snapshots or offsets determine the result.", "Do not put credentials or raw sensitive payloads in a manifest.", "Do not promise replay after the source retention horizon has passed."],
    ["data-engineering/dag-intervals-and-idempotent-tasks", "data-engineering/pipeline-lineage-and-impact-analysis", "data-engineering/pipeline-slos-and-error-budgets", "data-engineering/backfill-publication-boundary", "data-engineering/billing-pipeline-operations-project", "data-science/reproducible-analysis-snapshot"], "Orchestration and production operations")

add("billing-pipeline-operations-project", "Project: operate a daily billing pipeline",
    "Release a daily billing DAG whose readiness checks, retry rules, lineage, SLO and replay manifest survive a late source and an uncertain export acknowledgement.", [
    ("Specify the product", "Finance needs one committed bill total per account and event day by 08:30. The grain is account plus day; input orders and exchange rates arrive in separate bounded manifests. A missing source interval blocks publication. An empty but complete order interval is valid and yields a zero-row fact with an explicit completion marker, not an invented carry-forward total."),
    ("Build the DAG", "Create readiness tasks for both sources, a transform pinned to their snapshot IDs, a uniqueness and sum reconciliation task, a snapshot commit, and an export task keyed by interval and output snapshot. A late rate source should leave yesterday's published snapshot untouched. [[data-engineering/dag-intervals-and-idempotent-tasks|Idempotent task outputs]] make a retry converge instead of appending another bill."),
    ("Inject three failures", "First, send half a source batch without its completion manifest; no transform should run. Second, make one account produce a duplicate business key; quarantine or fail the candidate, keeping the last good snapshot. Third, let the export receiver accept the file but drop the acknowledgement; a retry must use the same idempotency key and produce one remote artifact. [[data-engineering/failure-classification-and-retry-budget|Retry policy]] should stop on the duplicate-key defect."),
    ("Evaluate the consumer promise", "For each interval, calculate whether complete inputs, quality and publication met 08:30. Keep source lag and processing duration as separate diagnostics. Record a run manifest with input snapshots, code digest, counts, output snapshot and export key; emit lineage to the finance report. [[data-engineering/pipeline-slos-and-error-budgets|The SLO]] counts a late but correct interval as late, and an on-time wrong interval as bad."),
    ("Deliver a release packet", "Include an interval diagram, a contract for each source, the retry table, a manifest from one successful run, evidence for all three injected failures, a query that checks one-row-per-account-day, and an operator action for each alert. Run an exact replay from retained inputs and compare the canonical output digest. If a source version is unavailable, name the limit rather than asserting reproducibility.")],
    '''from collections import defaultdict

order_rows = [
    {"account": "acct-47", "day": 47, "amount_cents": 7300},
    {"account": "acct-47", "day": 47, "amount_cents": 2500},
    {"account": "acct-83", "day": 47, "amount_cents": 4100},
]

def bill_totals(records):
    totals = defaultdict(int)
    for record in records:
        if record["amount_cents"] < 0:
            raise ValueError("negative order amount requires separate refund flow")
        totals[(record["account"], record["day"])] += record["amount_cents"]
    return dict(totals)

totals = bill_totals(order_rows)
assert totals[("acct-47", 47)] == 9800
assert sum(totals.values()) == sum(row["amount_cents"] for row in order_rows)''',
    "Aggregation is O(N) expected time and O(A) space for N orders and A account-day keys. Production cost includes pinned input retention, validation scans, transactional publication, monitoring and occasional replay. A fast transform is not a successful release if its source or export boundary is unverified.",
    ["Do not treat an incomplete batch as a legitimate zero-row interval.", "Do not retry an export with a new key after an uncertain acknowledgement.", "Do not call a scheduler-green run good when its published totals fail reconciliation."],
    ["data-engineering/dag-intervals-and-idempotent-tasks", "data-engineering/dependency-readiness-and-source-freshness", "data-engineering/pipeline-lineage-and-impact-analysis", "data-engineering/pipeline-slos-and-error-budgets", "data-engineering/failure-classification-and-retry-budget", "data-engineering/replay-manifest-and-audit-trail", "data-engineering/receipt-pipeline-replay-project"], "Orchestration and production operations", True)


def publish():
    rows = json.loads(FIXTURE.read_text())
    paths = {item["path"] for item in lessons}
    assert len(paths) == len(lessons)
    rows = [row for row in rows if row["path"] not in paths]
    by_path = {row["path"]: row for row in rows}
    titles = {path: row["title"] for path, row in by_path.items()}
    titles.update({item["path"]: item["title"] for item in lessons})
    now = datetime.datetime.now(datetime.UTC).isoformat()

    def prose(value):
        return re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
                      lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
                      html.escape(value))

    def link_list(targets):
        return "<ul>" + "".join('<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>" for target in targets) + "</ul>"

    for index, item in enumerate(lessons):
        body = "<p>" + html.escape(item["summary"]) + "</p>"
        for heading, paragraph in item["sections"]:
            body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(paragraph) + "</p>"
        body += ('<h2>Implementation</h2><pre><code class="language-python">' + html.escape(item["code"]) +
                 "</code></pre><h2>Performance and operating cost</h2><p>" + html.escape(item["cost"]) +
                 "</p><h3>Common Mistakes</h3><ul>" +
                 "".join("<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]) +
                 "</ul><h2>Read next</h2>" + link_list(item["related"]))
        path = item["path"]
        row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
                   type="article", path=path, title=item["title"], summary=item["summary"], body=body,
                   category="AI & Data", subject="data-engineering-project" if item["project"] else "data-engineering",
                   difficulty="Advanced", tags=["ai-data", "data-engineering"], potd_date=None,
                   featured=False, sort_order=7820 + index, status="published", published_at=now,
                   created_at=now, updated_at=now,
                   data={"subject_root": HUB, "section_path": PROJECT_HUB if item["project"] else HUB,
                         "content_format": "html", "seo_ready": True,
                         "kind": "project" if item["project"] else "tutorial",
                         "reading_minutes": max(5, len(re.sub(r"<[^>]+>", " ", body).split()) // 180),
                         "author_path": "authors/aitrove-editorial",
                         "verification_suite": "Editorial, code and internal-link checks",
                         "related": [{"path": target, "title": titles[target]} for target in item["related"]]})
        rows.append(row)
        by_path[path] = row

    hub = by_path[HUB]
    project_hub = by_path[PROJECT_HUB]
    module_titles = ["Storage contracts and table design", "Orchestration and production operations"]
    project_headings = ["Versioned order-lake release project", "Daily billing operations project"]
    for module_title, project_heading in zip(module_titles, project_headings):
        tutorial_paths = [item["path"] for item in lessons if item["module"] == module_title and not item["project"]]
        project_paths = [item["path"] for item in lessons if item["module"] == module_title and item["project"]]
        assert len(tutorial_paths) == 6 and len(project_paths) == 1
        if not any(module["title"] == module_title for module in hub["data"]["modules"]):
            hub["data"]["modules"].insert(-1, {"title": module_title,
                                              "summary": "A connected release path from contract to verified operation.",
                                              "lessons": tutorial_paths})
        apply_module = next(module for module in hub["data"]["modules"] if module["title"] == "Apply your knowledge")
        if project_paths[0] not in apply_module["lessons"]:
            apply_module["lessons"].append(project_paths[0])
        if "<h2>" + module_title + "</h2>" not in hub["body"]:
            hub["body"] += "<h2>" + module_title + "</h2>" + link_list(tutorial_paths)
            hub["body"] += "<h2>" + project_heading + "</h2>" + link_list(project_paths)
        if project_paths[0] not in project_hub["data"]["modules"][0]["lessons"]:
            project_hub["data"]["modules"][0]["lessons"].append(project_paths[0])
        if "<h2>" + project_heading + "</h2>" not in project_hub["body"]:
            project_hub["body"] += "<h2>" + project_heading + "</h2>" + link_list(project_paths)
    hub["updated_at"] = now
    project_hub["updated_at"] = now

    crosslinks = [
        ("data-engineering/source-contract-and-raw-landing", "data-engineering/schema-compatibility-and-consumer-rollout"),
        ("data-engineering/incremental-watermark-and-ties", "data-engineering/dag-intervals-and-idempotent-tasks"),
        ("data-engineering/cdc-replay-and-deletes", "data-engineering/deletion-propagation-and-erasure-proof"),
        ("data-engineering/idempotent-load-and-checkpoint", "data-engineering/failure-classification-and-retry-budget"),
        ("data-engineering/event-time-and-late-arrivals", "data-engineering/partition-planning-and-skew"),
        ("data-engineering/quality-quarantine-and-reconciliation", "data-engineering/dependency-readiness-and-source-freshness"),
        ("data-engineering/warehouse-history-asof-join", "data-engineering/lakehouse-snapshot-and-atomic-commit"),
        ("data-engineering/backfill-publication-boundary", "data-engineering/replay-manifest-and-audit-trail"),
        ("data-engineering/receipt-pipeline-replay-project", "data-engineering/versioned-order-lake-release-project"),
        ("streaming-analytics/streaming-analytics-tutorial", "data-engineering/dag-intervals-and-idempotent-tasks"),
        ("feature-stores/historical-point-in-time-join", "data-engineering/lakehouse-snapshot-and-atomic-commit"),
        ("data-science/reproducible-analysis-snapshot", "data-engineering/replay-manifest-and-audit-trail"),
        ("privacy-aware-ml/privacy-aware-ml-tutorial", "data-engineering/deletion-propagation-and-erasure-proof"),
        ("mlops/mlops-tutorial", "data-engineering/pipeline-slos-and-error-budgets"),
    ]
    for source, target in crosslinks:
        source_row = by_path[source]
        anchor = ('<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' +
                  html.escape(titles[target]) + "</a>.</p>")
        if anchor not in source_row["body"]:
            source_row["body"] += anchor
            source_row["data"].setdefault("related", []).append({"path": target, "title": titles[target]})
            source_row["updated_at"] = now

    assert len({row["path"] for row in rows}) == len(rows)
    FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"new_articles": len(lessons), "new_projects": 2,
                      "crosslinks_from_existing": len(crosslinks)}))


if __name__ == "__main__":
    publish()

"""Add event-time session and lake-file-layout learning paths."""
from de_batch_publisher import publish

SESSIONS = 'Session windows and late merge repair'
LAYOUT = 'Lake file layout and measured data skipping'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='data-engineering/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('session-window-gap-and-late-bridge', 'Session-window gaps and late bridges',
    'A late event can connect two activity sessions that were already reported separately; session boundaries therefore need an explicit correction contract.', [
    ('Define the gap before assigning IDs', 'For each account, consecutive events belong to one session when the event-time gap is at most eleven minutes. Equality is intentional. The records at 09:00 and 09:22 start separate sessions; an event at 09:11 bridges them. Process arrival order does not decide membership. A user-facing timeout may differ from this analytical gap, so name the clock and key in the contract. [[data-engineering/event-time-and-late-arrivals|Event-time handling]] explains why ingestion order alone produces inconsistent groups.'),
    ('Keep enough state to find a bridge', 'A session operator must retain intervals or their event membership while an accepted late event could extend an endpoint or connect neighboring intervals. Closing the first result at its current end is not the same as forgetting it. Measure watermark progress for every source partition, and publish the latest time at which an event can still merge a session. [[data-engineering/watermark-retention-and-late-corrections|Retention policy]] sets the boundary for later replay.'),
    ('Publish revisions, not independent totals', 'Suppose two provisional sessions have totals of 74 and 51 units. A bridging event worth 9 units produces one corrected total of 134. Emitting 134 while keeping 74 and 51 active makes a dashboard count 259. Retire both former result identities, then publish the merged result. A sink that lacks retract or upsert semantics requires a versioned replacement table and a serving pointer rather than append-only rows.'),
    ('Treat boundary changes as identity changes', 'Using the current start timestamp as a permanent session ID fails when an earlier late event extends the start. Give each published session a revision and track which earlier outputs it supersedes. A stable identity can be derived from immutable event membership for a particular revision, but a merge still creates a new identity and must remove the two old ones. [[data-engineering/join-replay-output-identity-and-recovery|Replay-safe output identity]] provides a related correction pattern.'),
    ('Test both late and too-late paths', 'Deliver the 09:11 bridge after both initial results have fired but before allowed lateness expires; expect one active merged row. Deliver the same event after state expires; expect a replay request or a documented rejection, never a silent third session. Add duplicate event IDs, equal-gap boundaries, a stalled partition and a hot account. Compare the final table against a batch recomputation from unique source events.')],
    '''from datetime import datetime, timedelta, timezone

def group_sessions(activity_events, gap):
    ordered = sorted(activity_events, key=lambda event: (event[1], event[0]))
    sessions = []
    for event_id, event_at, amount in ordered:
        if not sessions or event_at - sessions[-1]["end"] > gap:
            sessions.append({"start": event_at, "end": event_at,
                             "event_ids": [event_id], "amount": amount})
        else:
            session = sessions[-1]
            session["end"] = event_at
            session["event_ids"].append(event_id)
            session["amount"] += amount
    return sessions

base = datetime(2026, 10, 6, 9, tzinfo=timezone.utc)
activity = [("activity-47", base, 74),
            ("activity-83", base + timedelta(minutes=22), 51)]
assert len(group_sessions(activity, timedelta(minutes=11))) == 2
activity.append(("activity-61", base + timedelta(minutes=11), 9))
merged = group_sessions(activity, timedelta(minutes=11))
assert len(merged) == 1 and merged[0]["amount"] == 134''',
    'Sorting N events for a bounded replay costs O(N log N) time and O(N) space. An indexed streaming implementation can inspect neighboring sessions under one key instead, but the retained state, timers and correction records increase with active sessions and permitted lateness. A longer grace interval improves repair coverage while raising checkpoint size and delaying finality.',
    ['Do not use processing-time arrival order as the event-time session boundary.', 'Do not append a merged total while its two superseded totals remain active.', 'Do not assume a late bridge can be repaired after all contributing state has been discarded.'],
    ['data-engineering/event-time-and-late-arrivals', 'data-engineering/watermark-retention-and-late-corrections', 'data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/session-revisions-and-sink-retractions', 'data-engineering/customer-activity-session-project'], SESSIONS)

add('session-revisions-and-sink-retractions', 'Session revisions and sink retractions',
    'A session result is a changing claim over event membership, so replay and late merging need explicit supersession records at the sink.', [
    ('Separate event identity from result identity', 'Deduplicate source events by immutable event ID before grouping. A result ID derived from sorted member IDs and a rule version identifies one exact session revision, but adding or bridging an event changes that ID. Store the prior published IDs for the same account and interval, then replace them as one logical commit. [[data-engineering/event-envelope-identity-and-tombstones|Event envelopes]] define source revisions and tombstones upstream.'),
    ('Make the correction atomic to readers', 'When a late bridge merges sessions A and B into C, publish deletion markers for A and B and the upsert for C in one transaction or one candidate generation. If the storage system cannot make that group atomic, expose a generation pointer only after all three changes are durable. Readers should never see A, B and C as simultaneously current. An audit stream may retain every revision, but serving queries must filter to current rows.'),
    ('Control duplicate trigger firings', 'An early trigger, an event-time trigger and a late firing may emit the same membership more than once. The sink should key by a deterministic result identity or by a stable logical key plus revision, and an attempt should carry a monotonic generation. Replaying the same checkpoint and source offsets must leave the same current table. A new event legitimately changes membership and must not be suppressed by a dedupe key based only on account ID.'),
    ('Repair expired sessions elsewhere', 'Once a session has passed its accepted lateness and state has been cleaned, a historical correction cannot safely pass through the current live window. Route the affected account and interval to a bounded rebuild from raw events. Compute a candidate set, compare counts and amounts with the published generation, then switch readers. [[data-engineering/backfill-publication-boundary|Atomic backfill publication]] avoids mixed old and new results.'),
    ('Prove accounting invariants', 'For every input generation, each unique source event belongs to exactly one current session per key. Current session totals must sum to the accepted unique event amounts, even after a bridge and replay. Validate that no deleted revision remains current, and preserve the mapping from superseded IDs to the replacement ID. These checks catch a sink that accepts the new row but loses one of the two retractions.')],
    '''import hashlib

def session_revision(account_id, event_ids, rule_version):
    members = sorted(set(event_ids))
    payload = "|".join([account_id, rule_version] +
                       [f"{len(event_id)}:{event_id}" for event_id in members])
    return hashlib.sha256(payload.encode()).hexdigest()

first_id = session_revision("account-29", ["activity-47"], "gap-11-v2")
second_id = session_revision("account-29", ["activity-83"], "gap-11-v2")
merged_id = session_revision("account-29",
                             ["activity-47", "activity-61", "activity-83"],
                             "gap-11-v2")
current = {first_id: 74, second_id: 51}
for stale_id in (first_id, second_id):
    current.pop(stale_id)
current[merged_id] = 134
assert current == {merged_id: 134}
assert session_revision("account-29",
                        ["activity-83", "activity-61", "activity-47"],
                        "gap-11-v2") == merged_id''',
    'Building an ID from M member IDs costs O(M log M) time for sorting and O(M) temporary space. A production operator may maintain incremental membership state, but the sink still needs merge or transaction support and an index on current IDs. Audit history grows with every revision; bound its retention separately from the live serving table.',
    ['Do not use account ID alone as a dedupe key for all sessions.', 'Do not expose the replacement before the obsolete results are retired.', 'Do not mistake repeat trigger firings for distinct activity.'],
    ['data-engineering/session-window-gap-and-late-bridge', 'data-engineering/join-replay-output-identity-and-recovery', 'data-engineering/backfill-publication-boundary', 'data-engineering/replay-manifest-and-audit-trail', 'data-engineering/customer-activity-session-project'], SESSIONS)

add('customer-activity-session-project', 'Project: recover late customer activity sessions',
    'Build an event-time session table that repairs late bridges, retracts old results and survives checkpoint replay without double counting.', [
    ('Create a controlled event feed', 'Generate 470 unique activity events across 29 accounts with an eleven-minute inactivity gap and three minutes of accepted lateness. Include two sessions separated by 22 minutes and a bridge at their shared eleven-minute boundary. Inject a duplicate event ID, one event just beyond the gap, a late event after finality and an idle partition. Record source offsets and event timestamps independently of arrival times.'),
    ('Implement the live session operator', 'Key by account and merge event-time intervals when neighboring gaps are at most eleven minutes. Track one watermark per input partition, timer state and active session counts. Publish provisional results only if the sink supports later retractions. Keep a clear rule for when a session is final, and demonstrate that a stalled partition can delay that declaration without changing which records belong together. [[data-engineering/session-window-gap-and-late-bridge|Gap semantics]] drive the expected answer.'),
    ('Add an atomic correction sink', 'After the bridge arrives, retract both former session revisions and publish one merged revision. Crash after preparing the correction but before checkpoint acknowledgement, then replay the same offsets. The current table must contain one merged session with the exact unique-event total. Test a second crash after the sink commit, where retry must detect the already applied generation. [[data-engineering/session-revisions-and-sink-retractions|Revision identity]] makes those attempts comparable.'),
    ('Handle the expired correction', 'Send an event beyond accepted lateness into a dated repair queue. Rebuild the affected account interval from retained raw events into a candidate generation, compare membership and totals, and switch the serving pointer only after validation. Record a deliberate failed candidate and show the last-good table remains available. Do not change the live watermark backward to force the event into an expired window.'),
    ('Submit proof from both views', 'Deliver the arrival-order trace, final event-time grouping, retraction log, generation pointer, checkpoint positions, current-table uniqueness check and batch reconciliation. Report state peak for the hot account and the count of side-output late records. Include a negative run that appends the merged row without retiring the originals; its overcount should be visible in the test result.')],
    '''from datetime import datetime, timedelta, timezone

base = datetime(2026, 10, 6, 9, tzinfo=timezone.utc)
arrival_order = [
    ("activity-47", base, 74),
    ("activity-83", base + timedelta(minutes=22), 51),
    ("activity-61", base + timedelta(minutes=11), 9),
    ("activity-61", base + timedelta(minutes=11), 9),
]
unique_events = {event_id: (event_at, amount)
                 for event_id, event_at, amount in arrival_order}
ordered = sorted(unique_events.values())
groups = []
for event_at, amount in ordered:
    if not groups or event_at - groups[-1]["end"] > timedelta(minutes=11):
        groups.append({"end": event_at, "amount": amount})
    else:
        groups[-1]["end"] = event_at
        groups[-1]["amount"] += amount
assert len(groups) == 1
assert groups[0]["amount"] == sum(value[1] for value in unique_events.values()) == 134''',
    'The reference recomputes N accepted events in O(N log N) time and O(N) space. A keyed streaming operator reduces repeated full sorting at the cost of retained per-account session state and correction metadata. Measure state bytes, checkpoint duration and sink commits under the hot-account fixture; replay cost depends on the oldest repairable raw-event offset.',
    ['Do not count the duplicate bridge twice.', 'Do not let a crash expose both old and merged revisions as current.', 'Do not hide a too-late event by silently moving the watermark backward.'],
    ['data-engineering/session-window-gap-and-late-bridge', 'data-engineering/session-revisions-and-sink-retractions', 'data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/watermark-retention-and-late-corrections', 'data-engineering/streaming-risk-ledger-project'], SESSIONS, True)


add('lake-file-statistics-and-skip-safety', 'Lake file statistics and safe data skipping',
    'File and row-group bounds can eliminate irrelevant reads, but missing or stale statistics must never eliminate a matching record.', [
    ('Start with the query predicate', 'A query for orders from account 47 can skip a file only when trustworthy statistics prove its account range excludes 47. A file with minimum 40 and maximum 60 remains a candidate even if it contains no 47; bounds allow false positives, not false negatives. Null predicates need their own null counts or explicit uncertainty. [[data-engineering/parquet-row-groups-and-column-pruning|Row-group and column pruning]] happens at a different layer from skipping entire files.'),
    ('Bind bounds to the committed file', 'Collect minimum, maximum, null count and record count from the actual written data, then attach them to the file version referenced by the committed snapshot. A rewritten file needs new statistics; copying old bounds to new content is unsafe. Files whose statistics are absent, truncated or computed with incompatible comparison rules remain candidates. A scan engine may still choose to read more than the minimum safe set for planning reasons.'),
    ('Respect types and comparison rules', 'String ordering, decimal scale, timezone normalization and case folding can alter how a predicate compares with stored bounds. Treat a type migration as a statistics-contract change. If a query casts an account ID to text while the file stores an integer range, do not apply integer pruning unless the planner proves equivalence. [[data-engineering/cross-engine-sql-semantic-differences|Cross-engine semantic differences]] make a plan from one engine insufficient proof for another.'),
    ('Measure actual pruning', 'Record files listed, files rejected by metadata, row groups read, bytes fetched and query time for a fixed workload. A file-level skip ratio of 90 percent may still be poor if the remaining files are wide or contain most rows. Compare cold and warm runs separately, and pin the same snapshot for baseline and candidate so concurrent appends cannot manufacture a gain. Missing statistics should be visible as a reason, not folded into a generic scanned count.'),
    ('Keep deletion semantics intact', 'A file that carries a matching value may still have those rows removed by delete files. Pruning must use the table format’s current snapshot and delete semantics, not a loose directory scan of physical objects. Rewrites and delete materialization can alter bounds. [[data-engineering/snapshot-safe-delete-rewrite|Snapshot-safe rewrite]] governs publication; the skip checker should validate candidate output against a full scan before promotion.')],
    '''def file_may_match(file_stats, lower_account, upper_account):
    minimum = file_stats.get("min_account")
    maximum = file_stats.get("max_account")
    if minimum is None or maximum is None:
        return True  # Unknown bounds must remain in the scan.
    return not (maximum < lower_account or minimum > upper_account)

committed_files = [
    {"file": "orders-47.parquet", "min_account": 41, "max_account": 53},
    {"file": "orders-83.parquet", "min_account": 71, "max_account": 91},
    {"file": "orders-61.parquet"},
]
candidates = [item["file"] for item in committed_files
              if file_may_match(item, 47, 47)]
assert candidates == ["orders-47.parquet", "orders-61.parquet"]''',
    'Testing F file metadata records costs O(F) time and O(C) output space for C candidates; manifest indexes can reduce planning work for selective partitions. Statistical collection adds write CPU and metadata bytes. A false positive costs an extra read, while a false negative loses data, so an uncertain bound must default to scanning.',
    ['Do not discard a file merely because it lacks statistics.', 'Do not reuse pre-rewrite bounds for newly written bytes.', 'Do not interpret a high skip ratio as a correctness test.'],
    ['data-engineering/parquet-row-groups-and-column-pruning', 'data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/snapshot-safe-delete-rewrite', 'data-engineering/workload-driven-clustering-and-drift', 'data-engineering/order-lake-layout-release-project'], LAYOUT)

add('workload-driven-clustering-and-drift', 'Workload-driven clustering and layout drift',
    'Physical ordering should be chosen from observed predicates and maintained only while its read savings exceed rewrite and write costs.', [
    ('Pick from real query shapes', 'Inspect a representative week of filters, joins and scanned bytes. If most selective requests constrain account ID within a day, daily partitioning plus account clustering may outperform adding a separate partition for every account. Too many tiny partitions multiply metadata and writer work. Do not choose a clustering key merely because it has many distinct values; verify that the query engine stores usable bounds and actually applies the predicate. [[data-engineering/lake-file-statistics-and-skip-safety|Safe skipping]] is the mechanism being purchased.'),
    ('Compare layouts on the same snapshot', 'Build a candidate layout from one pinned generation and run the same cold and warm queries against both layouts. Capture planning time, listed files, bytes read, CPU and end-to-end latency. Check selective equality filters, broad scans, writes and maintenance jobs. A single fast dashboard query does not justify a rewrite if ingest latency and storage amplification harm the rest of the workload.'),
    ('Detect decay from new writes', 'Fresh append files may arrive unsorted even when older partitions are tightly grouped. As their share grows, min/max ranges overlap and skip efficiency falls. Track candidate files per predicate over time, along with file sizes and overlap, and schedule maintenance when projected read waste exceeds rewrite cost. [[data-engineering/compaction-retention-and-replay-horizon|Compaction]] manages file count; sorting addresses locality, so measure both independently.'),
    ('Budget rewrite side effects', 'A sort rewrite consumes shuffle, I/O and temporary storage. It may increase write amplification or conflict with concurrent appends, and it must preserve row values, deletes and snapshot visibility. Choose a bounded subset such as recent high-traffic days, publish it atomically, and keep the prior generation available until verification. Avoid a daily full-table rewrite if only a small tail is responsible for query degradation.'),
    ('Set an exit rule', 'Define the minimum saved bytes or latency per rewrite hour, the largest allowed writer lag, and the maximum query regression for broad scans. Revisit key choice when the workload changes. A former account-filter workload may become a time-range workload, making the old clustering expensive but ineffective. Store the benchmark data with the release so a later operator can reverse the choice rather than defending it by habit.')],
    '''query_weights = {
    "account_lookup": 47,
    "regional_rollup": 29,
    "full_scan": 8,
}
baseline_bytes = {
    "account_lookup": 920,
    "regional_rollup": 680,
    "full_scan": 1200,
}
candidate_bytes = {
    "account_lookup": 145,
    "regional_rollup": 510,
    "full_scan": 1200,
}

def weighted_scan_cost(weights, bytes_by_query):
    return sum(count * bytes_by_query[query_name]
               for query_name, count in weights.items())

saved_mb = (weighted_scan_cost(query_weights, baseline_bytes)
            - weighted_scan_cost(query_weights, candidate_bytes))
rewrite_mb = 19_000
assert saved_mb == 47 * 775 + 29 * 170
assert saved_mb > rewrite_mb''',
    'For Q query classes, weighted cost comparison is O(Q) time and O(1) extra space, but the measured workload is the hard part. Sort maintenance may read and write every selected file, often with shuffle and temporary duplicate storage. Its benefit depends on predicate selectivity, statistics availability and how quickly new writes degrade locality.',
    ['Do not add high-cardinality partitions just to imitate clustering.', 'Do not compare layouts using different table snapshots or cache states.', 'Do not ignore unsorted append files when reporting a one-time benchmark.'],
    ['data-engineering/lake-file-statistics-and-skip-safety', 'data-engineering/partition-planning-and-skew', 'data-engineering/compaction-retention-and-replay-horizon', 'data-engineering/optimistic-table-commits-and-conflicts', 'data-engineering/order-lake-layout-release-project'], LAYOUT)

add('order-lake-layout-release-project', 'Project: release a measured order-lake layout',
    'Rebuild a bounded order-lake partition with verified file bounds, benchmark it against the same snapshot and publish only a net-positive layout.', [
    ('Construct the baseline', 'Generate 47,000 orders across 29 days and 83 accounts. Keep order IDs unique, add null customer regions and several wide text attributes, then write files with overlapping account ranges. Record committed snapshot ID, file count, min/max/null statistics and query workload. Include an account equality lookup, a day-and-account filter, a regional rollup and a full scan. [[data-engineering/lake-file-statistics-and-skip-safety|The skip rules]] decide which files remain candidates.'),
    ('Build a bounded candidate', 'Retain day as the partition key; sort recent high-traffic days by account ID within a bounded file-size target. Do not repartition to one directory per account. Regenerate statistics from candidate bytes and verify that all old rows remain represented under the table format’s delete semantics. A writer racing with the rewrite should trigger conflict handling or a new candidate rather than silently replacing its fresh rows.'),
    ('Benchmark without moving the goalposts', 'Pin source and candidate snapshots that contain the same logical rows. Run each query with both cold and warm cache conditions, collect listed files, skipped files, row groups, bytes read and elapsed time, and repeat enough times to see variance. Measure candidate write time and storage amplification. [[data-engineering/workload-driven-clustering-and-drift|The workload decision]] uses weighted costs, not one cherry-picked fast lookup.'),
    ('Publish through a release gate', 'Compare row counts, checksums by day, delete behavior and query answers. Reject the candidate if any result differs, even if its skip ratio looks excellent. Commit the new file set atomically, retain the previous snapshot through the rollback window, and record file IDs and rewrite attempt in a manifest. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Snapshot publication]] keeps readers on one complete generation.'),
    ('Monitor what happens next', 'Append an intentionally unsorted day and show the skip ratio falling for that day. Derive a threshold for another bounded maintenance pass using read waste and rewrite cost. Submit the baseline and candidate manifests, benchmark table, validation output, conflict trace, release pointer and rollback test. A static layout screenshot is not evidence that the new writes remain efficient.')],
    '''file_ranges = [
    ("orders-a.parquet", 21, 39),
    ("orders-b.parquet", 40, 58),
    ("orders-c.parquet", 59, 83),
    ("orders-unknown.parquet", None, None),
]

def candidate_files(account_id, ranges):
    return [file_name for file_name, minimum, maximum in ranges
            if minimum is None or maximum is None
            or minimum <= account_id <= maximum]

assert candidate_files(47, file_ranges) == [
    "orders-b.parquet", "orders-unknown.parquet"]
baseline_order_ids = {"order-47", "order-61", "order-83"}
candidate_order_ids = {"order-83", "order-47", "order-61"}
assert candidate_order_ids == baseline_order_ids''',
    'The file-metadata filter is O(F) for F files; a real rewrite sorts N selected records in roughly O(N log N) comparison time and needs shuffle or external-spill capacity. Candidate files temporarily duplicate storage until old snapshots expire. Report net read savings over the expected query volume against that rewrite, metadata, write-lag and storage cost.',
    ['Do not release a candidate that changes query answers.', 'Do not compute new bounds from a sample and then prune with them as if complete.', 'Do not report performance without pricing the rewrite and unsorted future appends.'],
    ['data-engineering/lake-file-statistics-and-skip-safety', 'data-engineering/workload-driven-clustering-and-drift', 'data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/optimistic-table-commits-and-conflicts', 'data-engineering/versioned-order-lake-release-project'], LAYOUT, True)


CROSSLINKS = [
    ('data-engineering/event-time-and-late-arrivals', 'data-engineering/session-window-gap-and-late-bridge'),
    ('data-engineering/watermark-retention-and-late-corrections', 'data-engineering/session-window-gap-and-late-bridge'),
    ('data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/session-revisions-and-sink-retractions'),
    ('data-engineering/join-replay-output-identity-and-recovery', 'data-engineering/session-revisions-and-sink-retractions'),
    ('data-engineering/streaming-risk-ledger-project', 'data-engineering/customer-activity-session-project'),
    ('data-engineering/backfill-publication-boundary', 'data-engineering/customer-activity-session-project'),
    ('data-engineering/parquet-row-groups-and-column-pruning', 'data-engineering/lake-file-statistics-and-skip-safety'),
    ('data-engineering/snapshot-safe-delete-rewrite', 'data-engineering/lake-file-statistics-and-skip-safety'),
    ('data-engineering/partition-planning-and-skew', 'data-engineering/workload-driven-clustering-and-drift'),
    ('data-engineering/compaction-retention-and-replay-horizon', 'data-engineering/workload-driven-clustering-and-drift'),
    ('data-engineering/versioned-order-lake-release-project', 'data-engineering/order-lake-layout-release-project'),
    ('data-engineering/optimistic-table-commits-and-conflicts', 'data-engineering/order-lake-layout-release-project'),
]


if __name__ == '__main__':
    publish(LESSONS, (SESSIONS, LAYOUT), CROSSLINKS,
            'aitrove-data-engineering-sessions-layout-import-20261006.json', 7940)

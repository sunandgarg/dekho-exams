"""Add original Data Engineering lessons on event evolution and recovery."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'src/data/fixtures.json'
HUB = 'data-engineering/data-engineering-tutorial'
PROJECT_HUB = HUB + '/project'
EVOLVE = 'Event contracts and concurrent tables'
RECOVER = 'Regional recovery and query serving'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='data-engineering/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('schema-registry-transitive-compatibility', 'Schema registry and transitive compatibility',
    'A schema registry stores versioned event contracts; a compatibility rule decides which historic payloads a new reader can still decode.', [
    ('Define the reader horizon', 'A payment topic can retain 47 days of events while consumers replay from their own older checkpoints. Checking a proposed schema only against the immediately previous version is insufficient if a reader can encounter any version in the retained log. Choose a transitive rule when the complete retained history must remain readable. [[data-engineering/schema-compatibility-and-consumer-rollout|Consumer rollout]] still needs separate semantic checks after wire compatibility passes.'),
    ('Name the subject deliberately', 'A registry subject may follow a topic, a record type or another product boundary. The name controls which versions are compared and who may publish them. If unrelated events share one subject, a harmless change to one can block another. If related events use unrelated subjects, a consumer can miss a breaking shift. Record the subject strategy in the source contract.'),
    ('Test actual old bytes', 'A rule saying a new field is optional does not prove that a production reader handles every older payload, nested default and unknown enum. Keep a small, authorized replay corpus with event bytes and schema identifiers from each supported version. Decode it in CI with the candidate reader. Measure whether the resulting business values still satisfy null, currency and event-time contracts.'),
    ('Stage both deployment directions', 'Backward compatibility usually protects a new reader consuming old data; it does not automatically protect an old reader from a new writer. Roll out readers before producers when that is the safe direction for the chosen rule. A long-lived offline consumer may require a dual-publish window or a new topic. [[data-engineering/dataset-ownership-and-change-approval|Owners and consumers]] should approve the semantic transition.'),
    ('Stop irreversible changes early', 'Removing a required field, reusing a field identifier or changing cents to a floating currency value can break old data or corrupt meaning even when some decoders accept it. Register schemas in a controlled release step, reject incompatible versions before production writes, and preserve the schema ID with each event so replay never guesses which decoder to use.')],
    '''schema_versions = [
    {"version": 1, "required": {"payment_id", "amount_cents"}},
    {"version": 2, "required": {"payment_id", "amount_cents"}},
    {"version": 3, "required": {"payment_id", "amount_cents", "currency"}},
]

def reads_all_versions(reader_fields, historic_versions):
    return all(contract["required"].issubset(reader_fields)
               for contract in historic_versions)

assert reads_all_versions({"payment_id", "amount_cents", "currency"}, schema_versions)
assert not reads_all_versions({"payment_id", "currency"}, schema_versions)
''',
    'This simplified set check costs O(V × F) time for V retained versions and up to F required fields per version, with O(F) reader metadata. A real registry applies format-specific compatibility rules to full schemas, and a replay corpus also incurs decoding CPU and storage. Limit the corpus to representative supported versions while retaining enough history to catch a non-transitive break.',
    ['Do not assume a check against the latest version protects older retained data.', 'Do not equate wire compatibility with unchanged business meaning.', 'Do not deploy a new producer before checking old consumers under the selected rule.'],
    ['data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/event-envelope-identity-and-tombstones', 'data-engineering/optimistic-table-commits-and-conflicts', 'data-engineering/order-event-migration-project', 'data-engineering/source-contract-and-raw-landing'], EVOLVE)

add('event-envelope-identity-and-tombstones', 'Event envelopes, identity and tombstones',
    'An event envelope carries routing and replay metadata around the business payload; a tombstone makes a deletion explicit to downstream consumers.', [
    ('Separate three identities', 'An order event needs a stable event ID for deduplication, an entity key for partitioning and the source position for ordered replay. These values answer different questions. Two updates to one order share the entity key but must not share the event ID. A retransmission of the same update keeps its event ID. [[data-engineering/cdc-replay-and-deletes|CDC replay]] uses source order to settle conflicting updates.'),
    ('Carry a versioned payload', 'The envelope should include event type, schema identifier, source namespace, event time and publication time. A consumer can then decode the payload without inferring its shape from a nullable field. Keep business identifiers and raw payload only where classification allows them. [[data-engineering/data-classification-and-access-boundaries|Access boundaries]] must cover dead-letter storage because malformed envelopes often contain the original sensitive event.'),
    ('Make deletion unambiguous', 'A null amount is not an order deletion. Emit an explicit delete operation or a key plus tombstone according to the stream contract. The consumer removes or marks the entity at the ordered source position, then records the delete in a replay manifest. If an older update arrives later, source-order checks must prevent resurrection. [[data-engineering/deletion-propagation-and-erasure-proof|Erasure proof]] extends this into retained snapshots and replicas.'),
    ('Bound duplicate memory', 'Retaining every event ID forever makes state grow with lifetime throughput. Define a deduplication horizon at least as long as the supported retry and replay window, or use source position and per-entity ordering where that is sufficient. State what happens to a duplicate outside the horizon. An event log retained for months cannot rely on a one-day ID cache for exact historical replay.'),
    ('Test reorder and compaction', 'Send update A, delete B, retransmit A and then update C for the same entity. The final state should reflect C only if C is a legitimate later source operation. When compacting a keyed log, preserve tombstone retention long enough for lagging readers; removing it too early can leave a stale copy alive downstream.')],
    '''events = [
    {"event_id": "evt-47", "order_id": "ord-47", "position": 47, "op": "upsert", "cents": 4200},
    {"event_id": "evt-48", "order_id": "ord-47", "position": 48, "op": "delete"},
    {"event_id": "evt-47", "order_id": "ord-47", "position": 47, "op": "upsert", "cents": 4200},
]

def replay_order(records):
    state, latest, seen = {}, {}, set()
    for event in records:
        if event["event_id"] in seen:
            continue
        seen.add(event["event_id"])
        key = event["order_id"]
        if event["position"] <= latest.get(key, -1):
            continue
        latest[key] = event["position"]
        if event["op"] == "delete":
            state.pop(key, None)
        else:
            state[key] = event["cents"]
    return state

assert replay_order(events) == {}''',
    'A keyed replay is O(N) expected time for N events and uses O(E + K) state for retained event IDs and K entity positions. A compacted topic reduces old payload volume but cannot replace the source audit log when exact change history matters. Tombstone retention and deduplication state must cover the slowest supported consumer.',
    ['Do not use the entity key as the unique event ID.', 'Do not interpret a nullable business value as a deletion.', 'Do not expire tombstones before a lagging consumer can observe them.'],
    ['data-engineering/cdc-replay-and-deletes', 'data-engineering/deletion-propagation-and-erasure-proof', 'data-engineering/schema-registry-transitive-compatibility', 'data-engineering/order-event-migration-project', 'data-engineering/replay-manifest-and-audit-trail'], EVOLVE)

add('optimistic-table-commits-and-conflicts', 'Optimistic table commits and write conflicts',
    'An optimistic table writer reads a snapshot, prepares new files and attempts an atomic metadata commit; a competing commit may force validation or retry.', [
    ('Name the read and write sets', 'A nightly account correction reads account-day rows and replaces the affected partition. A second writer appends new account-day rows. Whether they conflict depends on table isolation and which files or predicates each writer touched. Recording only the target table name is too coarse. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Atomic publication]] makes each successful version visible at once, but does not settle conflicting intentions.'),
    ('Do not blindly replay a failed commit', 'If writer A validates against snapshot 47 while writer B commits snapshot 48 first, A may need to recompute against 48. Reusing A’s old candidate files without checking the new table state can discard B’s rows or violate uniqueness. Distinguish a safe metadata retry from a business transformation that must be rerun. Pin source inputs and record the base snapshot.'),
    ('Keep attempts off the reader path', 'Candidate files are not published merely because they exist. The commit points readers to one accepted metadata generation. An abandoned writer can leave unreferenced files; remove them only after in-flight attempts and rollback windows are ruled out. [[data-engineering/task-retries-and-atomic-partition-output|Task attempt selection]] handles this lower boundary.'),
    ('Choose a conflict policy by grain', 'Two independent appends to disjoint partitions may both succeed after revalidation. Two updates to the same order version cannot be merged by appending both unless the product explicitly keeps both versions. Define unique keys and affected predicates, then fail or serialize competing changes that alter the same logical row. A retry that silently changes which correction wins is a semantic decision.'),
    ('Exercise concurrent release', 'Start two writers from the same snapshot. Commit the first, force the second to validate against the new metadata, and assert either a correct rebase or an explicit conflict. Verify only one current snapshot pointer, complete files, unchanged unrelated partitions and a manifest naming both attempts. Measure orphan cleanup separately from commit success.')],
    '''table = {"version": 47, "rows": {"ord-47": 4200}}

def commit_update(current, base_version, order_id, cents):
    if current["version"] != base_version:
        raise RuntimeError("snapshot changed; recompute before commit")
    next_rows = dict(current["rows"])
    next_rows[order_id] = cents
    return {"version": base_version + 1, "rows": next_rows}

first = commit_update(table, 47, "ord-48", 1900)
try:
    commit_update(first, 47, "ord-47", 4300)
except RuntimeError:
    pass
else:
    raise AssertionError("stale writer committed")
assert first["rows"] == {"ord-47": 4200, "ord-48": 1900}''',
    'The reference copy costs O(K) time and space for K rows; real table formats avoid copying all data by writing changed files and a new metadata tree. Conflict validation adds metadata reads and may force repeated compute. Under contention, the cost of discarded candidate files and recomputation can dominate the small atomic pointer swap.',
    ['Do not treat prepared files as committed rows.', 'Do not retry a stale business transform without revalidating its read set.', 'Do not delete abandoned files while another writer can still reference them.'],
    ['data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/task-retries-and-atomic-partition-output', 'data-engineering/compaction-retention-and-replay-horizon', 'data-engineering/order-event-migration-project', 'data-engineering/replay-manifest-and-audit-trail'], EVOLVE)

add('order-event-migration-project', 'Project: migrate an order event contract safely',
    'Release a new order-event schema while preserving older readers, deletion semantics and atomic warehouse snapshots under concurrent writes.', [
    ('Freeze the current contract', 'Collect supported event schema IDs, retained source positions, consumer versions and one authorized replay fixture per version. Document event ID, namespaced order key, event time and delete operation separately. State the last checkpoint from which each consumer may restart. [[data-engineering/schema-registry-transitive-compatibility|Transitive compatibility]] must cover that replay horizon.'),
    ('Introduce the new field', 'Add a nullable fulfillment region with a documented unknown value. Register the proposed schema only after old payloads decode in the candidate reader and old readers accept newly written events under the selected compatibility mode. If either direction fails, stage a dual-reader or new-topic migration instead of changing a registry setting to hide the failure.'),
    ('Replay changes deterministically', 'Feed an upsert, an order correction, a delete and a delayed retransmission. Apply source positions so the old upsert cannot resurrect the deleted order. Retain the event ID and schema ID in the audit row. [[data-engineering/event-envelope-identity-and-tombstones|Envelope rules]] make retry and delete behavior visible to the warehouse loader.'),
    ('Publish through a conflict gate', 'Build a candidate mart snapshot from pinned input positions. Start an unrelated append writer from the same base version, commit it first, then force the migration writer to revalidate. It must either recompute against the new snapshot or fail cleanly; it must never replace the append. Verify one current pointer and no reader-visible candidate files.'),
    ('Hand over proof', 'Deliver the old and new schema contracts, compatibility result against all supported versions, replay output, deletion check, competing-writer transcript and committed manifest. Include a rollback plan that restores the old reader without losing the new producer events, or explicitly state why rollback requires a compensating migration.')],
    '''order_events = [
    {"id": "evt-71", "order": "ord-71", "position": 71, "op": "upsert", "cents": 6300},
    {"id": "evt-72", "order": "ord-71", "position": 72, "op": "delete"},
    {"id": "evt-71", "order": "ord-71", "position": 71, "op": "upsert", "cents": 6300},
]

def materialize(records):
    latest, values = {}, {}
    for event in records:
        key = event["order"]
        if event["position"] <= latest.get(key, -1):
            continue
        latest[key] = event["position"]
        if event["op"] == "delete":
            values.pop(key, None)
        else:
            values[key] = event["cents"]
    return values

assert materialize(order_events) == {}''',
    'Replay is O(N) expected time and O(K) entity state for N events and K order keys. Registry checks, candidate table files and concurrent validation add release cost. The project accepts that overhead to prevent a lower-cost migration from making historical events unreadable or dropping a competing writer’s valid rows.',
    ['Do not change compatibility policy merely to pass one release.', 'Do not let a delayed event resurrect a deleted order.', 'Do not publish a candidate snapshot before conflict validation.'],
    ['data-engineering/schema-registry-transitive-compatibility', 'data-engineering/event-envelope-identity-and-tombstones', 'data-engineering/optimistic-table-commits-and-conflicts', 'data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/lakehouse-snapshot-and-atomic-commit'], EVOLVE, True)

add('data-pipeline-rpo-rto-and-replication-lag', 'Pipeline RPO, RTO and replication lag',
    'A recovery point objective bounds acceptable data loss; a recovery time objective bounds how long a data product may remain unavailable after a failure.', [
    ('Define the product boundary', 'A replicated object store alone does not make a complete analytics service recoverable. Include source offsets, checkpoint state, table metadata, access policy, schema versions and serving configuration in the recovery unit. If a replica has files but not the snapshot pointer that names them, the reader cannot safely publish the newest data. [[data-engineering/replay-manifest-and-audit-trail|The release manifest]] should identify every required component.'),
    ('Measure lag at the last consistent point', 'A monitor reporting five minutes of object replication lag does not prove five-minute RPO if table metadata or checkpoints trail by 42 minutes. Track the newest complete generation that can be opened and validated in the recovery region. RPO is the age of that generation at failure time. Record source high-water marks and a digest for each release.'),
    ('Include activation in RTO', 'Recovery time starts with detection and includes operator decision, credential availability, restore, data validation, route switch and the first successful consumer query. A runbook that times only instance startup understates the outage. Define what degraded mode is acceptable, such as serving a clearly dated last-good snapshot while new ingestion catches up.'),
    ('Avoid split-brain writes', 'If both regions resume publishing after a network partition, two independent snapshot histories can emerge. Use a single writer lease with a monotonically increasing epoch or another fencing mechanism. [[data-engineering/failover-writer-fencing-and-source-positions|Fenced promotion]] prevents the old writer from committing after the recovery writer takes control.'),
    ('Prove the target in a drill', 'Disable the primary in a controlled exercise, restore from a selected generation and run real consumer queries. Measure last consistent input position, actual missing events, elapsed recovery time and post-restore backlog. A backup is evidence of stored bytes; a successful query and reconciliation are evidence of a usable data product.')],
    '''from datetime import datetime, timezone

failure_at = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
last_complete = datetime(2026, 10, 6, 11, 37, tzinfo=timezone.utc)
first_query = datetime(2026, 10, 6, 12, 41, tzinfo=timezone.utc)

def recovery_minutes(failure, recoverable, query_ready):
    if not recoverable <= failure <= query_ready:
        raise ValueError("recovery times are out of order")
    return ((failure - recoverable).total_seconds() / 60,
            (query_ready - failure).total_seconds() / 60)

assert recovery_minutes(failure_at, last_complete, first_query) == (23, 41)''',
    'The arithmetic is O(1), but the recovery design pays for replicated bytes, retained checkpoints, standby compute, drills and catch-up processing. A smaller RPO generally requires faster complete-generation replication; a smaller RTO requires more prepared capacity and fewer manual activation steps. Measure both against a working consumer query.',
    ['Do not use file replication lag as the only measure of recoverable data age.', 'Do not time RTO from instance boot instead of failure detection.', 'Do not promote a second writer without fencing the first.'],
    ['data-engineering/failover-writer-fencing-and-source-positions', 'data-engineering/serving-index-and-freshness-contract', 'data-engineering/regional-analytics-recovery-project', 'data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/replay-manifest-and-audit-trail'], RECOVER)

add('failover-writer-fencing-and-source-positions', 'Failover writer fencing and source positions',
    'Writer fencing rejects commits from a former primary after another region takes ownership; source positions let the replacement resume without a gap or double publication.', [
    ('Give each promotion a higher epoch', 'A coordinator issues monotonically increasing writer epochs from durable control storage. Every table commit carries its epoch, and the commit gate rejects an older one. A lease timeout alone is not enough: a paused old worker can wake after its lease expires and still send writes. The epoch makes that stale writer observable and rejectable.'),
    ('Promote from a complete generation', 'The recovery region first selects one manifest whose data files, schema IDs, state and source positions are present. It must not resume from the newest source offset if the table snapshot reflects an older offset. Replaying the intervening events under stable event IDs should reconstruct the missing result. [[data-engineering/event-envelope-identity-and-tombstones|Envelope identity]] supplies the deduplication boundary.'),
    ('Separate duplicate delivery from duplicate effects', 'After promotion, some source records may be delivered again. This is acceptable if the sink’s business key and version rule reject repeated effects. A side channel such as an email or billing call needs its own idempotency contract. [[streaming-analytics/idempotent-sink-and-replay|Sink replay]] cannot be inferred from the table commit alone.'),
    ('Handle the returning primary', 'When the old region recovers, it must not automatically resume as writer. Reconcile its last epoch and committed snapshot with the promoted region, then either discard candidate outputs or replay missing source intervals into the new leader. A second promotion back is a controlled release with a still higher epoch. Keep both branches for audit until divergence is resolved.'),
    ('Inject delayed acknowledgements', 'Pause the primary immediately before commit, promote the secondary, commit one new generation, then release the old request. The old commit must fail because its epoch is lower. Validate one current table pointer, no missing source positions and unchanged financial totals. Record the rejected attempt and candidate-file cleanup path.')],
    '''published = {"epoch": 8, "source_position": 470, "total_cents": 8200}

def fenced_commit(current, epoch, source_position, total_cents):
    if epoch < current["epoch"]:
        raise PermissionError("stale writer epoch")
    if source_position < current["source_position"]:
        raise ValueError("source position moved backward")
    return {"epoch": epoch, "source_position": source_position,
            "total_cents": total_cents}

promoted = fenced_commit(published, 9, 471, 9100)
try:
    fenced_commit(promoted, 8, 472, 10200)
except PermissionError:
    pass
else:
    raise AssertionError("former primary committed")
assert promoted["source_position"] == 471''',
    'The reference gate is O(1) time and space. A real implementation must make epoch comparison and table pointer update atomic in durable storage; a read followed by an unguarded write is unsafe. Replicated source logs, candidate files and promotion drills add storage and compute, but prevent two regions from publishing competing histories.',
    ['Do not trust a time-based lease without a stale-writer commit check.', 'Do not resume from an offset newer than the recoverable table generation.', 'Do not let a returning primary reclaim writer status automatically.'],
    ['data-engineering/data-pipeline-rpo-rto-and-replication-lag', 'data-engineering/event-envelope-identity-and-tombstones', 'data-engineering/optimistic-table-commits-and-conflicts', 'data-engineering/regional-analytics-recovery-project', 'data-engineering/replay-manifest-and-audit-trail'], RECOVER)

add('serving-index-and-freshness-contract', 'Serving indexes and freshness contracts',
    'A serving index organizes released data for specific queries; its freshness contract states which published generation each answer represents.', [
    ('Start from a measured query', 'An operations dashboard needs account-day totals by account ID and recent day. A columnar fact table may scan efficiently for broad analytics but still be slow for one account. Build a keyed serving index or materialized view for that access pattern, and preserve the source snapshot ID with each indexed row. [[data-engineering/fact-grain-and-measure-additivity|Fact grain]] determines whether one key maps to one result or many.'),
    ('Publish index generations together', 'Loading an index record by record exposes mixed snapshots while the warehouse table stays atomic. Build a new index generation from one table snapshot, validate count and digest, then switch one reader pointer. During rebuild, the previous generation can continue serving with an explicit as-of time. [[data-engineering/lakehouse-snapshot-and-atomic-commit|Snapshot publication]] supplies the underlying transaction boundary.'),
    ('Define acceptable staleness', 'Freshness is not simply job success. Measure source event time, table publish time, index publish time and query time. A dashboard may promise data no more than 18 minutes behind the latest accepted source interval. If that target fails, show the last-good timestamp or stop the query according to its use. [[data-engineering/pipeline-slos-and-error-budgets|Pipeline SLOs]] need the consumer-visible age.'),
    ('Plan update and repair paths', 'Late corrections and dimension repairs can change prior account-day results. The index must replace the same logical key using a higher source generation, not append a second amount. Keep a reverse map or partition manifest to target affected keys. When a full rebuild is cheaper or safer, publish it atomically and compare a sample of queries against the warehouse snapshot.'),
    ('Budget the extra copy', 'An index speeds selected queries at the cost of storage, refresh compute and another failure surface. Watch write amplification, hot keys, p95 query latency and index lag. If all consumers perform broad scans, a specialized index may add cost without benefit. The serving design should be justified by the actual read workload, not by a generic low-latency goal.')],
    '''warehouse_rows = [
    {"account": "acct-47", "day": 47, "cents": 5200},
    {"account": "acct-83", "day": 47, "cents": 1800},
]

def build_index(rows, snapshot_id):
    index = {}
    for row in rows:
        key = (row["account"], row["day"])
        if key in index:
            raise ValueError("account-day grain violated")
        index[key] = {"cents": row["cents"], "snapshot": snapshot_id}
    return index

serving = build_index(warehouse_rows, "snap-47")
assert serving[("acct-47", 47)] == {"cents": 5200, "snapshot": "snap-47"}''',
    'Building a keyed index is O(N) expected time and O(N) extra storage for N warehouse rows; lookup is O(1) expected locally, subject to network and backend latency in production. Refresh work may duplicate the entire index per generation. Incremental updates reduce that cost but require stronger ordering and repair validation.',
    ['Do not serve a mixture of warehouse snapshot generations.', 'Do not claim freshness from a green job status alone.', 'Do not append a corrected key beside its old value.'],
    ['data-engineering/fact-grain-and-measure-additivity', 'data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/pipeline-slos-and-error-budgets', 'data-engineering/regional-analytics-recovery-project', 'data-engineering/data-pipeline-rpo-rto-and-replication-lag'], RECOVER)

add('regional-analytics-recovery-project', 'Project: recover a regional analytics mart',
    'Recover a customer-day mart in a secondary region while preserving source position, writer ownership and the serving view’s generation.', [
    ('Set measurable recovery targets', 'The product publishes a customer-day count and net cents every 24 minutes. Set an RPO of 36 minutes and an RTO of 68 minutes for the exercise, then define which consumer query proves recovery. The manifest must name source positions, table snapshot, schema versions, index generation and access-policy revision. [[data-engineering/data-pipeline-rpo-rto-and-replication-lag|The RPO/RTO contract]] applies to that complete set.'),
    ('Prepare the replica', 'Copy data files and table metadata to the secondary region, verify checksums, and retain the source log past the worst expected outage and catch-up duration. Build an index generation from each complete table snapshot. Do not publish a replica merely because files arrived; the metadata pointer and access policy must agree with them.'),
    ('Force a clean promotion', 'Stop primary writes at a chosen source position, simulate its loss and grant the secondary a higher writer epoch. Restore from the newest complete generation, replay missing source records and atomically publish the next table and index pointers. [[data-engineering/failover-writer-fencing-and-source-positions|Fencing]] must reject a delayed primary commit after promotion.'),
    ('Test the consumer path', 'Run account-day queries before failure, during last-good serving and after recovery. Every answer should name one index generation and its source cutoff. Compare aggregate cents and unique account-day keys with the source manifest; verify access roles still filter rows and mask fields correctly in the second region.'),
    ('Record the incident evidence', 'Deliver timestamps for failure detection, last recoverable generation and first successful query; calculate actual RPO and RTO. Include rejected old-writer attempt, replayed source interval, orphan candidates, index switch and cost of the drill. Reconcile the returning primary before any failback. A green infrastructure dashboard is not sufficient evidence of correct answers.')],
    '''from datetime import datetime, timezone

failure = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
complete = datetime(2026, 10, 6, 11, 35, tzinfo=timezone.utc)
query_ready = datetime(2026, 10, 6, 12, 54, tzinfo=timezone.utc)
target_rpo_minutes = 36
target_rto_minutes = 68

actual_rpo = (failure - complete).total_seconds() / 60
actual_rto = (query_ready - failure).total_seconds() / 60
assert actual_rpo == 25 and actual_rto == 54
assert actual_rpo <= target_rpo_minutes
assert actual_rto <= target_rto_minutes''',
    'The objective calculation is O(1), while the release costs include cross-region transfer, retained snapshots, replay compute, standby serving capacity and periodic drills. A full index rebuild is O(N) in customer-day rows and can dominate the measured RTO, so include it in the timed exercise rather than declaring recovery after the table alone opens.',
    ['Do not report RPO from the newest copied file instead of a complete generation.', 'Do not let the old region resume writes after secondary promotion.', 'Do not count a restored table as recovered while the consumer index or access policy is missing.'],
    ['data-engineering/data-pipeline-rpo-rto-and-replication-lag', 'data-engineering/failover-writer-fencing-and-source-positions', 'data-engineering/serving-index-and-freshness-contract', 'data-engineering/replay-manifest-and-audit-trail', 'data-engineering/row-policy-and-column-mask-tests'], RECOVER, True)


def publish():
    rows = json.loads(FIXTURE.read_text())
    new_paths = {item['path'] for item in LESSONS}
    assert len(new_paths) == len(LESSONS) == 8
    rows = [row for row in rows if row['path'] not in new_paths]
    by_path = {row['path']: row for row in rows}
    titles = {path: row['title'] for path, row in by_path.items()}
    titles.update({item['path']: item['title'] for item in LESSONS})
    now = datetime.datetime.now(datetime.UTC).isoformat()

    def prose(value):
        return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                      lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                      html.escape(value))

    def link_list(targets):
        return '<ul>' + ''.join('<li><a href="/' + target + '">' +
                              html.escape(titles[target]) + '</a></li>' for target in targets) + '</ul>'

    changed = set(new_paths) | {HUB, PROJECT_HUB}
    for index, item in enumerate(LESSONS):
        body = '<p>' + html.escape(item['summary']) + '</p>'
        for heading, paragraph in item['sections']:
            body += '<h2>' + html.escape(heading) + '</h2><p>' + prose(paragraph) + '</p>'
        body += ('<h2>Implementation</h2><pre><code class="language-python">' +
                 html.escape(item['code']) + '</code></pre>' +
                 '<h2>Performance and operating cost</h2><p>' + html.escape(item['cost']) +
                 '</p><h3>Common Mistakes</h3><ul>' +
                 ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) +
                 '</ul><h2>Read next</h2>' + link_list(item['related']))
        path = item['path']
        row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
                   type='article', path=path, title=item['title'], summary=item['summary'], body=body,
                   category='AI & Data', subject='data-engineering-project' if item['project'] else 'data-engineering',
                   difficulty='Advanced', tags=['ai-data', 'data-engineering'], potd_date=None,
                   featured=False, sort_order=7880 + index, status='published',
                   published_at=now, created_at=now, updated_at=now,
                   data={'subject_root': HUB, 'section_path': PROJECT_HUB if item['project'] else HUB,
                         'content_format': 'html', 'seo_ready': True,
                         'kind': 'project' if item['project'] else 'tutorial',
                         'reading_minutes': max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                         'author_path': 'authors/aitrove-editorial',
                         'verification_suite': 'Editorial, code and internal-link checks',
                         'related': [{'path': target, 'title': titles[target]} for target in item['related']]})
        rows.append(row)
        by_path[path] = row

    hub = by_path[HUB]
    project_hub = by_path[PROJECT_HUB]
    hub['summary'] = 'Build replayable data products with explicit event contracts, atomic tables, governed access and tested recovery.'
    hub['body'] = re.sub(r'^<p>.*?</p>', '<p>' + hub['summary'] + '</p>', hub['body'], count=1)
    for module_title in (EVOLVE, RECOVER):
        lesson_paths = [item['path'] for item in LESSONS if item['module'] == module_title and not item['project']]
        project_paths = [item['path'] for item in LESSONS if item['module'] == module_title and item['project']]
        assert len(lesson_paths) == 3 and len(project_paths) == 1
        if not any(module['title'] == module_title for module in hub['data']['modules']):
            hub['data']['modules'].insert(-1, {'title': module_title,
                                               'summary': 'Verify the migration or recovery contract before completing the project.',
                                               'lessons': lesson_paths})
        practice = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
        if project_paths[0] not in practice['lessons']:
            practice['lessons'].append(project_paths[0])
        if '<h2>' + module_title + '</h2>' not in hub['body']:
            hub['body'] += '<h2>' + module_title + '</h2>' + link_list(lesson_paths)
            hub['body'] += '<h2>' + ('Order event migration' if module_title == EVOLVE else 'Regional analytics recovery') + '</h2>' + link_list(project_paths)
        if project_paths[0] not in project_hub['data']['modules'][0]['lessons']:
            project_hub['data']['modules'][0]['lessons'].append(project_paths[0])
        if project_paths[0] not in project_hub['body']:
            project_hub['body'] += '<h2>' + ('Order event migration' if module_title == EVOLVE else 'Regional analytics recovery') + '</h2>' + link_list(project_paths)
    hub['updated_at'] = now
    project_hub['updated_at'] = now

    crosslinks = [
        ('data-engineering/schema-compatibility-and-consumer-rollout', 'data-engineering/schema-registry-transitive-compatibility'),
        ('data-engineering/cdc-replay-and-deletes', 'data-engineering/event-envelope-identity-and-tombstones'),
        ('data-engineering/lakehouse-snapshot-and-atomic-commit', 'data-engineering/optimistic-table-commits-and-conflicts'),
        ('data-engineering/versioned-order-lake-release-project', 'data-engineering/order-event-migration-project'),
        ('data-engineering/replay-manifest-and-audit-trail', 'data-engineering/data-pipeline-rpo-rto-and-replication-lag'),
        ('data-engineering/keyed-state-checkpoints-and-recovery', 'data-engineering/failover-writer-fencing-and-source-positions'),
        ('data-engineering/pipeline-slos-and-error-budgets', 'data-engineering/serving-index-and-freshness-contract'),
        ('data-engineering/billing-pipeline-operations-project', 'data-engineering/regional-analytics-recovery-project'),
        ('data-engineering/streaming-risk-ledger-project', 'data-engineering/event-envelope-identity-and-tombstones'),
        ('data-engineering/stream-backpressure-and-catch-up-budget', 'data-engineering/data-pipeline-rpo-rto-and-replication-lag'),
        ('data-engineering/governed-customer-mart-project', 'data-engineering/serving-index-and-freshness-contract'),
        ('data-engineering/row-policy-and-column-mask-tests', 'data-engineering/regional-analytics-recovery-project'),
    ]
    for source, target in crosslinks:
        changed.add(source)
        row = by_path[source]
        anchor = ('<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' +
                  html.escape(titles[target]) + '</a>.</p>')
        if anchor not in row['body']:
            row['body'] += anchor
            row['data'].setdefault('related', []).append({'path': target, 'title': titles[target]})
            row['updated_at'] = now
    assert len({row['path'] for row in rows}) == len(rows)
    FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    import_path = ROOT / 'work/aitrove-data-engineering-evolution-recovery-import-20261006.json'
    import_path.write_text(json.dumps([by_path[path] for path in sorted(changed)], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_articles': len(LESSONS), 'new_projects': 2,
                      'crosslinks': len(crosslinks), 'import_rows': len(changed),
                      'import_path': str(import_path)}))


if __name__ == '__main__':
    publish()

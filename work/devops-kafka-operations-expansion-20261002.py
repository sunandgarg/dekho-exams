"""Add original Kafka operating-boundary lessons to local DevOps fixtures."""

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
project_hub = "devops/devops-tutorial/project"
quiz_hub = "devops/quizzes"
project_path = "devops/kafka-stream-recovery-project"
quiz_path = "quizzes/devops-kafka-operating-decisions"


def lesson(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    return dict(path="devops/" + slug, title=title, summary=summary,
                definition=definition, decision=decision, sample=sample,
                cost=cost, mistakes=mistakes, related=related)


specs = [
    lesson(
        "kafka-acks-isr-durability",
        "Kafka write durability: align acknowledgments with the in-sync replica floor",
        "A replicated topic is not a durability policy until producer and broker thresholds agree.",
        "A Kafka partition has a leader and replica followers. The in-sync replica set, or ISR, contains replicas close enough to the leader to qualify for an acknowledged write. The producer's acknowledgments setting and the topic's minimum ISR jointly decide whether a write succeeds during a broker fault. Replication factor describes assigned copies, not how many are currently in sync. This distinction matters during maintenance: a three-copy topic can temporarily have one eligible replica. An application that treats a successful send as a durable business event must record the exact producer and topic contract, then test the failure behavior.",
        "For a payment-event topic, assign three replicas, require two in-sync replicas, and use producer acknowledgments of all. If one broker is unavailable while two replicas remain in sync, writes may continue; if the ISR falls below two, writes fail instead of relaxing the policy silently. When all ISR members are unavailable, electing an out-of-sync replica can restore availability but may discard acknowledged history. Keep that choice explicit in the incident runbook. Producers must surface send failures to callers and retain an idempotent business request for retry. Measure ISR shrinkage, under-replicated partitions, producer errors, and the time taken to restore a replica before approving planned broker maintenance.",
        "Topic: payment-events\nReplication factor: 3\nmin.insync.replicas: 2\nProducer acks: all\nISR size 3: accept after all 3 ISR replicas acknowledge\nISR size 2: accept after both acknowledge\nISR size 1: reject the write",
        "Waiting for more replicas raises write latency and network work; a strict ISR floor can turn a replica outage into a write outage. That is an intentional trade. Capacity planning must leave disk, network, and broker headroom for follower catch-up; otherwise the system can remain below the write floor long after the initial fault is repaired. No setting promises zero loss under every correlated failure, disk fault, or incorrect operational intervention. Verify the actual client result, accepted offset, and post-failover record visibility in a disposable cluster rather than relying on a configuration screenshot.",
        ["Do not equate replication factor with current ISR size.", "Do not describe acks=all as an absolute zero-loss guarantee.", "Do not enable unclean leader election merely to clear an availability alert without accepting its loss risk."],
        ["devops/queue-consumer-reliability", "devops/partition-rebalance-safety", "devops/recovery-time-budget-ledger"],
    ),
    lesson(
        "kafka-producer-retry-ordering",
        "Kafka producer retries: preserve partition order without claiming end-to-end exactly-once",
        "A broker retry can be safe while a downstream side effect still runs twice.",
        "Kafka producer idempotence uses producer identity and sequence numbers to prevent duplicate append from a retried send within its supported scope. It does not deduplicate a new application request, a new producer identity, or a payment charged outside Kafka. Ordering is scoped to one partition. With idempotence disabled, retrying an earlier failed batch while a later batch is in flight can reverse their arrival order. The producer configuration must therefore be reviewed alongside record keys, retry deadlines, transaction boundaries, and the consumer's external effect ledger. A producer success callback means the configured broker acknowledgment contract was met; it does not prove a database update happened.",
        "An order service publishes status events keyed by order ID. Enable producer idempotence, compatible acknowledgments, and a finite delivery timeout. Record the business event ID in the payload. If a send outcome is ambiguous after a client timeout, retry the business operation through an outbox with a unique event ID rather than constructing a fresh, untracked event. A consumer that reserves inventory records the event ID in the same database transaction as its inventory change; a duplicate delivery then becomes a no-op. Transactions can atomically coordinate eligible Kafka writes and consumed offsets, but an HTTP call to a warehouse remains outside that Kafka transaction and needs its own idempotency contract.",
        "Record key: order-7284\nBusiness event ID: evt-38472\nProducer idempotence: enabled\nKafka transaction boundary: Kafka records and offsets only\nInventory ledger unique key: evt-38472\nHTTP warehouse call: separate idempotency key required",
        "Retries consume time, memory, network bandwidth, and broker capacity; high in-flight volume can enlarge the amount of work whose outcome is uncertain during a fault. A unique consumer ledger adds storage and indexed-write cost, but it makes replay and failover safer. Test a lost acknowledgment, a producer restart, and duplicate delivery separately. Measure both broker append duplicates and external effects. The two figures are different, and claiming exactly-once for the whole workflow when only Kafka writes are coordinated conceals a real billing or inventory risk.",
        ["Do not use a Kafka producer sequence number as a cross-service business ID.", "Do not assume producer idempotence prevents duplicate HTTP or database side effects.", "Do not infer global order across different partitions."],
        ["devops/transactional-outbox-delivery", "devops/object-event-ordering-idempotency", "devops/event-schema-evolution"],
    ),
    lesson(
        "kafka-retention-replay-budget",
        "Kafka retention: size the replay window against the longest recovery path",
        "Retention is a recovery deadline as well as a storage limit.",
        "A Kafka topic with delete retention removes old log segments according to time and size limits. Consumer offsets do not pin those records indefinitely. A consumer that remains offline past the available start offset cannot recover the missing interval by resetting its group. Retention therefore belongs in the service recovery contract, not just the broker storage configuration. Capacity calculations must account for ingress bytes, replication, compaction or segment overhead, and recovery traffic. A time target alone can be defeated by a smaller size cap; a size cap alone can be exhausted during a traffic burst.",
        "For a settlement stream receiving an expected 47 GiB per day, a four-day replay requirement implies 188 GiB of logical new records before replication, overhead, safety margin, and burst allowance. Three replicas create substantially more physical storage demand. A two-day consumer outage still leaves only two days of headroom if traffic follows the forecast. Set alerts on the oldest available offset, consumer lag in time, and disk growth, then rehearse restoration from a snapshot when the log window is insufficient. When increasing retention, verify available broker capacity and the time needed to rebalance data. When reducing it, notify every replay-dependent consumer and preserve an alternate archive first.",
        "Expected ingress: 47 GiB/day\nRequired replay horizon: 4 days\nLogical new-record floor: 47 x 4 = 188 GiB\nReplica count: 3\nPhysical new-record floor before overhead: 564 GiB\nAdd burst, segments, reassignments, and disk safety margin",
        "Longer retention buys more recovery time but costs disk, replica transfer, and potentially longer catch-up after a broker loss. A small segment can improve deletion granularity while increasing file-management overhead; an active segment is not removed merely because an individual record is old. Compare the oldest retained record with the oldest needed restore point, not just a configured duration. A group lag metric of zero can also mislead if an operator reset the group to latest and skipped unrecovered events. Prove record continuity with source sequence or business IDs.",
        ["Do not assume committed offsets preserve records past topic retention.", "Do not size only the leader's disk while ignoring replicas and rebalance headroom.", "Do not reset to latest to hide a consumer that fell beyond the retained window."],
        ["devops/queue-age-scaling-contract", "devops/cdc-snapshot-stream-handoff", "devops/recovery-time-budget-ledger"],
    ),
    lesson(
        "kafka-compaction-tombstone-window",
        "Kafka log compaction: rebuild state without resurrecting deleted keys",
        "A compacted topic preserves recent keyed state, but a new reader must see deletion markers in time.",
        "Kafka log compaction eventually removes superseded records with the same key while retaining a recent value for keys still present. It does not immediately rewrite every segment or guarantee that a consumer sees only one record per key. A record with a key and null value is a tombstone: it says the key was deleted. Tombstones are themselves eligible for removal after the configured delete-retention interval. A reader rebuilding a complete materialized view from the beginning must finish its scan within a compatible window, or an old value can be observed without its later deletion marker. The application still needs an explicit snapshot and restore contract.",
        "A customer-preferences view stores events keyed by customer ID. Key 7284 receives region west, then region north, then a null-value tombstone when the account is removed. A fresh view should end without key 7284. The operator measures full-bootstrap duration using the slowest realistic reader, including pauses and throttling, then chooses tombstone retention with headroom beyond that duration. It also tests a new reader from offset zero while the cleaner runs. If rebuilding takes longer than the tombstone window, use a consistent external snapshot with a captured stream position or increase the window; changing compaction frequency alone does not solve the deletion race.",
        "key=customer-7284, value={region: west}\nkey=customer-7284, value={region: north}\nkey=customer-7284, value=null  # tombstone\nExpected rebuilt state: customer-7284 absent\nReader bootstrap duration must fit deletion-marker window",
        "Compaction spends broker CPU, disk I/O, and temporary disk space. Larger tombstone windows preserve deletion evidence longer but also consume storage. A compacted topic is unsuitable as an immutable audit log because prior values may disappear; retain a separate history where the business requires it. Confirm the cleanup policy, key serialization, tombstone retention, and reader bootstrap time together. A null payload without the correct key is not a deletion of that customer's state. Observe cleaner backlog and materialized-view checksums under load before depending on a compacted topic for recovery.",
        ["Do not treat compaction as immediate per-key deduplication.", "Do not rebuild a state store without testing tombstone retention against scan duration.", "Do not use a compacted topic as the sole immutable history of every prior value."],
        ["devops/event-schema-evolution", "devops/cdc-snapshot-stream-handoff", "devops/kafka-retention-replay-budget"],
    ),
    lesson(
        "kafka-consumer-offset-recovery",
        "Kafka consumer offset recovery: preview every reset before changing a group",
        "An offset reset changes what the group will process next; it does not undo earlier side effects.",
        "A Kafka consumer group commits positions for its assigned partitions. Processing and committing are separate operations, so a crash can cause an already applied event to be delivered again, or a premature commit can skip an unapplied event. An operator-initiated reset moves the group's future read position within the currently retained log. It does not recreate expired records or reverse a database transaction. Recovery therefore requires a per-partition plan, an external-effect reconciliation strategy, and evidence of the exact old and proposed positions. A reset should be previewed while group members are stopped so a running consumer cannot race the change.",
        "A ledger consumer stops at offset 840 in partition two after malformed record 839. First capture the group state and output-ledger checkpoint. Fix the decoder or quarantine the poison event with its payload and reason; do not jump to latest. In a disposable rehearsal, reset only the affected topic and partition range to the chosen available offset, preview the new positions, and then execute after approval within the incident procedure. Restart a single consumer cohort and compare processed event IDs with ledger rows. If the record was already applied before the crash, its unique event ID prevents a second effect. Keep the old offsets and the CLI output in the incident evidence.",
        "Recovery record\nGroup: settlement-ledger-v2\nTopic/partition: settlement-events/2\nOld committed offset: 840\nProposed next offset: 839\nRetained earliest offset: 711\nAction: preview reset, execute while group inactive, replay with event-ID ledger\nAbort if retained earliest offset exceeds required replay start",
        "Replaying R retained records has O(R) application work and can load databases or external APIs much harder than normal consumption. Throttle the recovery cohort and watch output latency, duplicate rejection, partition lag, and broker fetch load. A reset to earliest may multiply this cost across every partition; scope the change narrowly. If the needed offset is gone, restore a consistent snapshot plus surviving tail rather than pretending the skipped events were processed. A dead-letter queue is useful only when its ownership, repair, and replay path are tested.",
        ["Do not run an offset reset against an active group.", "Do not use latest as a convenient way to clear lag.", "Do not assume a reset rolls back external side effects."],
        ["devops/partition-rebalance-safety", "devops/dead-letter-replay", "devops/queue-consumer-reliability"],
    ),
    lesson(
        "kafka-partition-key-capacity",
        "Kafka partition keys: balance throughput without breaking per-entity order",
        "A partition key is an ordering and capacity decision embedded in every produced event.",
        "Kafka orders records within one partition, not across an entire topic. Producers commonly route a stable key to one partition so updates for one entity preserve order. A key chosen only for semantic convenience can create a hot partition: one large tenant or status value receives most of the traffic while other partitions sit idle. Adding consumers cannot split work inside a single assigned partition. Increasing partition count may change key-to-partition mapping for later records, so records for one entity can cross old and new partitions during a migration. Treat partition count and key format as a versioned data contract.",
        "An invoice stream initially uses tenant ID as its key. One tenant produces 61 percent of writes, and its partition saturates while seven others remain underutilized. The service considers invoice ID as the new key because each invoice needs ordered state transitions, while cross-invoice order has no business meaning. Before switching, it checks that no consumer depends on tenant-wide order, dual-writes a shadow stream, and compares per-invoice state after replay. It assigns a new topic or deliberate migration boundary instead of simply expanding partitions under existing consumers. Scale-out estimates use the hottest partition rate, not the topic average.",
        "Current key: tenant ID; hottest tenant: 61% of writes\nRequired order: all updates for one invoice\nCandidate key: invoice ID\nMigration: new topic + shadow comparison + bounded cutover\nCapacity check: max partition ingress and consumer processing rate",
        "More partitions increase broker metadata, open files, replication work, rebalance time, and monitoring cardinality. A finer key spreads load only if traffic is actually distributed across those keys; a single invoice receiving all writes remains hot. Measure producer bytes and consumer processing time per partition, plus key distribution, before changing the contract. During migration, compare sequence numbers and final entity state, and define how late records on the old topic are drained. Avoid claiming exact per-key continuity if old and new topics process concurrently without a fencing or merge rule.",
        ["Do not assume adding consumers increases parallelism beyond active partition count.", "Do not change partition count without checking key routing and ordering consequences.", "Do not use a low topic-wide average to dismiss one saturated partition."],
        ["devops/partition-rebalance-safety", "devops/queue-age-scaling-contract", "devops/event-schema-evolution"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_path] = "Kafka stream recovery project: broker fault, replay, and state rebuild"
titles[quiz_path] = "Kafka operating decisions: durability, retention, and recovery quiz"
assert all(item["path"] not in by_path for item in specs)
assert project_path not in by_path and quiz_path not in by_path
assert all(target in titles for item in specs for target in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


related_paths = [item["path"] for item in specs]
for heading, summary, paths in [
    ("Kafka write and replay boundaries", "Connect producer acknowledgments, retry behavior, and retained-log recovery.", related_paths[:3]),
    ("Kafka state and consumer recovery", "Rebuild keyed state, reset offsets safely, and plan partition capacity.", related_paths[3:]),
]:
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "kafka", "stream-operations"],
               sort_order=25510 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 7,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in [*item["related"], project_path, quiz_path]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['decision'])}</p>"
        f'<pre><code class="language-text">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"], *related_paths[:2]])
        + "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    )
    rows.append(row)

project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title=titles[project_path],
               summary="Rehearse Kafka broker loss, duplicate sends, expired retention, tombstone rebuild, and offset recovery in a disposable cluster.",
               difficulty="Advanced", sort_order=25590,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 12,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related_paths]}
project["body"] = (
    "<p>Build a disposable three-broker stream for synthetic settlement and customer-preference events. Give the settlement topic three replicas and a two-replica write floor; put keyed customer state in a separate compacted topic. Record every generated event ID and expected final state outside the cluster before starting the fault drill. This project is a rehearsal, not a production change: isolate credentials, volumes, and network access so a reset or broker stop cannot affect live groups.</p>"
    "<h2>Establish the write boundary</h2><p>Publish 240 uniquely identified settlement records with idempotent producer behavior and acknowledgments of all. Stop one follower and confirm writes continue while two replicas remain in sync. Stop a second eligible replica; confirm the producer receives an error and the caller retains its request for retry. Restore replicas and verify accepted IDs from the surviving log. Do not claim the exercise succeeded merely because the producer process exited zero: compare broker records, caller receipts, and the external event ledger.</p>"
    "<pre><code class=\"language-text\">Synthetic acceptance\nSettlement records requested: 240 unique IDs\nAccepted IDs before fault: reconcile with broker log\nISR floor: 2 of 3 replicas\nBelow floor: write rejected, request retained for retry\nState rebuild: deleted customer key absent\nOffset reset: preview captured before execute; group inactive\nExpired replay start: restore snapshot plus surviving tail</code></pre>"
    "<h2>Inject replay faults</h2><p>Lose a producer acknowledgment and resend the same batch; compare broker append IDs with the business event ledger. Pause a consumer, let retained segments advance in the disposable topic, and show why a reset cannot recover records older than the earliest offset. Restore a known snapshot and replay the surviving tail without repeating external settlement effects. Seed a customer key with two values and a tombstone, then bootstrap a fresh view while the cleaner is active; it must end with the key absent. Record bootstrap duration against the configured deletion-marker window.</p>"
    "<h2>Change the partition contract</h2><p>Create a skewed stream where one tenant owns most writes. Measure per-partition ingress and consumer time; then shadow a new topic keyed by invoice ID. Compare per-invoice sequence and final state before declaring cutover. Finally stop the test consumer group, capture old and proposed offsets, preview a narrow reset, execute it, and start one cohort. Reconcile duplicates with unique business IDs. Archive the commands, observations, and rejected assumptions as the project evidence.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not run a reset while consumers are active.</li><li>Do not count rejected sends as accepted events.</li><li>Do not interpret a low topic average as proof that every partition has spare capacity.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*related_paths, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Kafka stream recovery drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("Three replicas exist but only one is in sync. What controls whether an acks=all write succeeds?", ["The minimum ISR floor", "The assigned replica count alone", "The consumer group name"], "A configured minimum ISR floor must be met for the write to succeed."),
    ("What does unclean leader election trade for availability?", ["Possible loss of records absent from the elected replica", "Faster compaction only", "Consumer key stability"], "An out-of-sync replica may lack acknowledged history."),
    ("What does producer idempotence cover?", ["Duplicate broker append from supported retried sends", "Every external HTTP payment", "All future requests using the same customer ID"], "Producer sequence handling has a narrower scope than business-effect deduplication."),
    ("Where is ordering guaranteed for ordinary keyed topic records?", ["Within their assigned partition", "Across every partition in the topic", "Across unrelated topics"], "The partition is Kafka's ordering unit."),
    ("A consumer is offline beyond retained history. Can an offset reset restore missing records?", ["No; use a consistent snapshot or archive plus surviving tail", "Yes; any committed offset pins the log", "Yes; reset to latest reconstructs them"], "A reset cannot recreate deleted segments."),
    ("Why check both retention time and size?", ["The tighter limit can end the replay window", "They always retain independent full copies", "Consumer commits disable size cleanup"], "Traffic bursts can exhaust a size cap early."),
    ("What does a null value with an existing key mean in a compacted topic?", ["A deletion tombstone", "A new partition", "A failed producer send"], "The keyed null marks removal of that key's state."),
    ("Why measure the full state-bootstrap duration?", ["The reader must observe tombstones before they are eligible for removal", "Compaction always finishes before a reader starts", "It replaces replication monitoring"], "A long scan can miss deletion evidence."),
    ("What is required before resetting a consumer group's offsets?", ["Stop its members and preview the proposed positions", "Increase its partition count", "Delete its output ledger"], "An active group can race the reset and obscure the recovery boundary."),
    ("What happens to a database effect when its Kafka offset moves backward?", ["It remains; replay needs an event-ID guard", "Kafka reverses the database transaction", "It becomes a tombstone"], "Kafka offsets do not control external state."),
    ("One tenant owns most records on a tenant-keyed topic. Why may more consumers fail to help?", ["The hot partition remains assigned to one consumer", "Kafka forbids new consumers", "Retention becomes infinite"], "Parallelism is limited by partition assignment and key skew."),
    ("What should accompany a key migration to a new topic?", ["Shadow comparison of per-entity sequence and final state", "Only a higher replica count", "Immediate deletion of the old topic"], "A changed routing contract can alter ordering and final state."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on Kafka durability, producer retries, retention, compaction, offsets, and partition keys.",
            sort_order=25600, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in related_paths],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Decide which Kafka boundary actually controls a write, replay, state rebuild, or partition migration. A successful command does not establish that downstream business state is correct.</p>"
    "<h2>Review these lessons</h2>" + links(related_paths)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-operations"])
    + "<h3>Common Mistakes</h3><ul><li>Do not confuse replica assignment with in-sync replicas.</li><li>Do not reset offsets to conceal lost business effects.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Kafka operating decisions</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for source, targets in {
    "devops/queue-consumer-reliability": [related_paths[0], related_paths[4]],
    "devops/transactional-outbox-delivery": [related_paths[1]],
    "devops/queue-age-scaling-contract": [related_paths[2], related_paths[5]],
    "devops/cdc-snapshot-stream-handoff": [related_paths[3]],
    "devops/partition-rebalance-safety": [related_paths[4], related_paths[5]],
    "devops/dead-letter-replay": [related_paths[4], project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Kafka operating follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1,
                  "total_records": len(rows)}))

"""Add original Redis operating-boundary lessons to DevOps fixtures."""

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
project_path = "devops/redis-recovery-boundaries-project"
quiz_path = "quizzes/devops-redis-operating-decisions"


def lesson(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    return dict(path="devops/" + slug, title=title, summary=summary,
                definition=definition, decision=decision, sample=sample,
                cost=cost, mistakes=mistakes, related=related)


specs = [
    lesson(
        "redis-persistence-recovery-window",
        "Redis persistence: state the recoverable write window before choosing AOF or snapshots",
        "A successful command response and a restorable disk image are different events.",
        "Redis persistence is an optional path from in-memory state to disk. RDB snapshots capture a point in time; writes after that snapshot are absent from that file. The append-only file, or AOF, records writes for replay and has a configurable synchronization policy. With periodic synchronization, a process or host failure may lose the most recent acknowledged writes. Running both mechanisms does not remove the need for a restore test: the chosen files must be copied consistently, kept off the failed host, and tested with the intended software version. A cache that can be rebuilt and an authoritative ledger need different recovery contracts.",
        "A pricing cache can accept a rebuild after restart, so its owner documents the source database and maximum refill rate. A reservation token store cannot casually regenerate lost tokens; the team either chooses a stricter persistence and replication design or moves the authoritative state to a transactional database. During a disposable drill, write 147 numbered keys, capture the last client acknowledgment, force a process and then host failure under the selected settings, and count which IDs restore. Repeat during AOF rewrite or RDB snapshotting. Inspect persistence status and error metrics before declaring the node healthy. Keep an off-host copy and a verified restore command in the runbook.",
        "Synthetic write range: reservation:1 through reservation:147\nClient receipt: last acknowledged ID and UTC time\nRestore evidence: highest contiguous ID recovered\nRDB boundary: latest completed snapshot\nAOF boundary: configured fsync behavior and last valid log\nDecision: compare observed loss with service recovery budget",
        "AOF adds disk writes and rewrite work; snapshotting consumes fork, copy-on-write memory, and storage bandwidth. A write-heavy instance can need material headroom while a background child runs. Stricter synchronization increases latency and does not make a replica failover transactionally consistent. Disk-full and failed rewrite conditions deserve alerts because an old snapshot can look normal while recent data is at risk. Measure recovery time as well as lost-write count: a large AOF can take longer to load than the service's restoration target allows.",
        ["Do not equate command acknowledgment with an off-host durable backup.", "Do not describe periodic AOF synchronization as zero-loss persistence.", "Do not enable a snapshot schedule without measuring fork and disk headroom."],
        ["devops/backup-and-recovery", "devops/immutable-backup-retention", "devops/recovery-time-budget-ledger"],
    ),
    lesson(
        "redis-maxmemory-eviction-contract",
        "Redis maxmemory: choose eviction behavior by the meaning of each key",
        "An eviction policy can turn memory pressure into a cache miss or a failed write.",
        "Redis maxmemory limits dataset growth under a selected eviction policy. With noeviction, writes that need more memory can fail while reads of existing keys continue. With an all-keys policy, Redis may remove cached keys to make room, shifting load toward the backing service. Policies restricted to expiring keys have a narrower candidate set; if too few keys qualify, writes can fail even though non-expiring keys occupy memory. The setting does not make every process allocation fit inside the dataset limit. Replication buffers, clients, allocator fragmentation, and persistence work also need memory headroom at the host or container boundary.",
        "A product catalog cache stores 2.3 million regenerable entries and shares the Redis instance with a small set of session tokens. Mixing the two makes allkeys eviction unsafe for sessions, while noeviction can turn a catalog traffic spike into write errors. Split the workloads or move session authority elsewhere. For the catalog cache, set a measured maxmemory budget and an all-keys eviction policy, then load 34 percent above the expected working set. Track evicted keys, hit ratio, miss latency, source-database QPS, resident memory, and rejected commands. Protect the backing database with bounded refill concurrency. A high hit ratio measured before eviction begins is not evidence that overload behavior is safe.",
        "Catalog: regenerable keys on dedicated cache\nSession token authority: separate store\nLoad test: 134% of forecast working set\nObserve: evictions, write errors, p99 miss latency, source QPS\nAbort: database refill exceeds its safe connection budget",
        "A larger memory limit buys a larger working set but increases failover transfer, snapshot size, and per-node cost. An eviction policy trades write availability for miss amplification; poor key-size distribution can make either outcome abrupt. Set alerts on used memory and resident memory separately, and include non-dataset allocations in the container limit. If a failed write affects business state, Redis should not be treated as an expendable cache. Rehearse a failover while near the limit, because replica promotion and persistence can consume additional headroom.",
        ["Do not share evictable catalog data with authoritative session state under one policy.", "Do not assume maxmemory equals total process memory.", "Do not celebrate eviction without checking database refill pressure."],
        ["devops/cache-stampede-control", "devops/container-oom-attribution", "devops/database-pool-pressure"],
    ),
    lesson(
        "redis-sentinel-failover-write-gap",
        "Redis Sentinel failover: reconcile acknowledged writes across a new primary",
        "Automatic promotion restores a writer endpoint but does not guarantee every prior write survived.",
        "Redis Sentinel monitors primary and replica instances and helps clients discover the current primary after failover. Redis replication is asynchronous, so a primary can acknowledge a write before a replica has it. If a lagging replica is promoted, a recently acknowledged write can disappear from the new primary. The old primary may later rejoin as a replica, replacing its divergent state. Sentinel is therefore an availability mechanism with an explicit write-gap risk, not a substitute for an authoritative transaction log. A client must discover the new primary through Sentinel-aware behavior and handle retries without inventing new business identities.",
        "A reservation service stores a temporary availability view in Redis but commits the actual reservation in a database. At 09:47, a primary failure occurs after Redis acknowledges token 7284; the promoted replica lacks it. The service reconstructs the view from the database ledger and rejects any action that relies only on the missing cache key. A disposable drill pauses replica traffic, issues numbered writes, kills the primary, and compares acknowledged IDs with the promoted dataset. It also reconnects clients through Sentinel discovery and confirms that stale connections do not continue to drive authoritative work on an old endpoint. Measure time to promotion, missing-write count, and database reconciliation time separately.",
        "Primary acknowledged: token-7284\nReplica before fault: through token-7282\nAfter promotion: reconcile token-7283 and token-7284\nAuthority: reservation database ledger\nClient action: discover current primary and retry by stable request ID\nRecovery evidence: missing IDs and rebuild duration",
        "Replication lag and failover time depend on load and network conditions. More replicas improve available promotion choices but do not make asynchronous writes atomic. A command such as WAIT can reduce the chance that an acknowledged write is absent from replicas, yet it does not create a strong-consistency guarantee or protect against every persistence and failover sequence. Monitor replica offsets, Sentinel quorum, client reconnect errors, and old-primary fencing. If losing one acknowledged write is unacceptable, choose an authority with the required durability model instead of describing Sentinel as lossless.",
        ["Do not promise lossless failover from asynchronous replicas.", "Do not treat a new primary address as proof that the application state reconciled.", "Do not retry an ambiguous reservation with a fresh business ID."],
        ["devops/failover-write-fencing", "devops/replica-lag-read-contract", "devops/redis-persistence-recovery-window"],
    ),
    lesson(
        "redis-cluster-slot-migration-clients",
        "Redis Cluster resharding: require redirect-aware clients and compatible key placement",
        "Moving a hash slot changes which node owns a key while requests are still arriving.",
        "Redis Cluster assigns keys to hash slots and places those slots on primary nodes. During a reshard, a client may receive MOVED for a settled location or ASK while a slot is being migrated. A client that treats either response as a normal application failure can turn maintenance into user errors; a client that never refreshes its slot map can keep sending traffic to old owners. Multi-key operations generally require their keys to reside in one slot. Hash tags can deliberately co-locate related keys, but concentrating too many hot keys in one slot creates a capacity ceiling that resharding cannot split without changing the key contract.",
        "A billing service atomically adjusts two counters for one account. It uses account-scoped hash tags for those counters, such as bill:{acct-7284}:used and bill:{acct-7284}:limit, after proving the two-key operation is required. In a disposable reshard drill, move the slot while 29 clients issue reads and updates. Record MOVED and ASK handling, retries, duplicate application effects, per-node latency, and final counter values. Clients must refresh routing and obey retry budgets. The team also measures the busiest account slot; if one account alone saturates a node, moving that slot merely relocates the hotspot. A new key model or workload split is needed.",
        "Keys: bill:{acct-7284}:used, bill:{acct-7284}:limit\nOperation: same-slot two-key update\nConcurrent clients: 29 during slot move\nExpected: redirect-aware retries; final counters reconcile\nHot-slot check: top account rate versus node capacity",
        "A reshard consumes network bandwidth, CPU, and key-movement time. Large values and hot slots increase the duration of mixed ownership. More cluster nodes do not reduce the cost of a single hot key or all keys trapped by one hash tag. Test the client library and configured retry deadlines under both redirect types rather than assuming an old client supports live migration. Maintain a stable business request ID across redirected retries when the update has effects outside Redis. Capacity planning should use per-slot and per-node tails, not only cluster-wide average utilization.",
        ["Do not use an ordinary single-node Redis client against a resharding cluster.", "Do not assume hash tags are free: they can create an unsplittable hotspot.", "Do not ignore multi-key slot requirements until production resharding."],
        ["devops/queue-age-scaling-contract", "devops/redis-maxmemory-eviction-contract", "devops/retry-timeout-budgets"],
    ),
    lesson(
        "redis-stream-pending-reclaim",
        "Redis Streams recovery: reconcile pending entries before trimming the log",
        "A consumer-group acknowledgment removes a pending reference, not the stream entry itself.",
        "Redis Streams consumer groups track delivered but unacknowledged entries in a pending entries list. A worker that crashes after a delivery leaves an entry pending; another worker can inspect and claim it after an appropriate idle interval. Claiming transfers responsibility, not proof that the previous worker failed before its external effect. A unique business event ID must guard the downstream effect before acknowledgment. Stream trimming is a separate storage action: removing an entry before every required consumer group has finished can leave a pending reference whose payload is unavailable. Retention must be sized against the slowest recovery path, not only the fastest group.",
        "A shipment projector reads stream shipments through group tracking-v2. Worker A writes projection event sh-7284, then crashes before XACK. Worker B waits beyond the measured normal processing interval, claims the idle entry, checks the projection's unique event receipt, and acknowledges without writing a second projection. The operator compares pending age, entry payload availability, last delivered ID, and projection count. A second analytics group has a longer replay window, so trim limits are chosen for that group too. If a required entry has already been trimmed, the team restores a snapshot and surviving stream tail rather than treating an empty payload as successful completion.",
        "Stream: shipments\nGroup: tracking-v2\nEvent ID: sh-7284\nWorker A: effect committed, acknowledgment missing\nWorker B: claim idle entry, check unique receipt, then XACK\nTrim gate: oldest required group recovery point remains available",
        "Scanning and claiming pending work costs Redis CPU and can flood a downstream system if a large backlog is released at once. Set the idle threshold above a realistic high percentile of processing time, then throttle claims. A threshold that is too short can make two healthy workers contend for the same effect. Track pending count and oldest pending age per group, not just stream length. Treat a trim policy as data deletion. Before shortening it, verify snapshots, lagging groups, and any consumer that is intentionally paused for maintenance.",
        ["Do not interpret a claim as proof the previous worker did no work.", "Do not trim a stream solely by its fastest consumer group.", "Do not acknowledge an unavailable payload as if it were processed."],
        ["devops/dead-letter-replay", "devops/queue-consumer-reliability", "devops/kafka-consumer-offset-recovery"],
    ),
    lesson(
        "redis-keyspace-notification-loss",
        "Redis keyspace notifications: keep correctness outside an ephemeral event channel",
        "A disconnected subscriber cannot replay missed keyspace notifications from Pub/Sub.",
        "Redis keyspace notifications publish selected changes and expirations over Pub/Sub. The channel is useful for hints, metrics, and local cache refreshes, but it is not a durable change log. A subscriber disconnected during an expiration or failover loses the event; after reconnect there is no built-in offset to replay it. Expiration notification timing is also not a business deadline guarantee because key deletion can be discovered later. A system that must invoice, refund, or release capacity after a timeout needs a durable source of truth and a reconciliation job. Notifications may wake the job early, but the job must also find missed work on its own.",
        "A reservation cache key expires after 47 minutes. A notification subscriber normally wakes a cleanup worker, but its connection drops for nine minutes during a broker restart. The authoritative reservation table stores expiry timestamps and state. Every two minutes, a bounded query finds overdue open reservations, marks them once through a conditional database update, and emits a unique release event. On reconnect, the subscriber resumes hint handling but does not assume it saw every expiration. The drill expires 83 synthetic keys during the disconnect and verifies all 83 reservations reach the intended state exactly once through reconciliation, without relying on a replayable Redis notification channel.",
        "Source of truth: reservation table with expiry and state\nRedis TTL: 47 minutes, advisory cache behavior\nSubscriber outage: 9 minutes\nMissed notifications: 83 synthetic expirations\nReconciler: every 2 minutes, bounded overdue query\nEffect key: reservation ID + release generation",
        "A reconciliation scan adds database read and write cost, so index expiry and state and process a capped batch. A long interval increases completion delay; a very short one can load the database unnecessarily. Measure backlog age and release count. Pub/Sub subscriptions also consume connection and network resources, so enable only event classes with a real consumer. This design deliberately tolerates duplicate hints: the conditional state transition decides whether the effect is new. If notifications are used for analytics, annotate data gaps during disconnects rather than treating the feed as complete history.",
        ["Do not make a keyspace notification the only trigger for a financial effect.", "Do not assume an expiration event fires exactly at the TTL deadline.", "Do not treat Pub/Sub reconnect as replay."],
        ["devops/cronjob-schedule-safety", "devops/scheduled-function-overlap-control", "devops/transactional-outbox-delivery"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_path] = "Redis recovery boundaries project: persistence, failover, resharding, and replay"
titles[quiz_path] = "Redis operating decisions: memory, failover, streams, and notifications quiz"
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
    ("Redis state and failover", "Compare persistence, memory pressure, and asynchronous promotion.", related_paths[:3]),
    ("Redis routing and recovery", "Test slot moves, pending stream work, and ephemeral notification gaps.", related_paths[3:]),
]:
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "redis", "data-operations"],
               sort_order=25910 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Rehearse Redis persistence loss, eviction, Sentinel promotion, Cluster resharding, stream claims, and missed notifications.",
               difficulty="Advanced", sort_order=25990,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 12,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related_paths]}
project["body"] = (
    "<p>Run this exercise in disposable Redis environments with synthetic reservation, catalog, and shipment data. Keep an external expected-state ledger before each fault. Do not use production credentials or assume one deployment topology supports every mode: a Sentinel replica drill and a Cluster slot migration need different isolated setups. The result is evidence about the chosen recovery contract, not a universal durability claim.</p>"
    "<h2>Test persistence and memory</h2><p>Write 147 numbered reservation keys, record the last acknowledged ID, and interrupt an instance during a background persistence operation. Restore from copied files and compare recovered IDs with receipts. Repeat a catalog-cache load at 134 percent of the forecast working set, observing evictions, write errors, resident memory, and source-database pressure. Keep authoritative reservations outside the evictable cache. The test fails if a memory policy silently removes a business token or if the backing database crosses its connection budget during refill.</p>"
    "<pre><code class=\"language-text\">Acceptance ledger\nPersistence: report highest contiguous restored ID of 147\nCache overload: observe eviction and backing-store p99\nSentinel failover: list acknowledged IDs absent after promotion\nCluster move: redirect-aware clients reconcile final counters\nStream crash: one effect despite pending redelivery\nNotification disconnect: 83 expirations reconciled from database</code></pre>"
    "<h2>Inject failover and routing changes</h2><p>Pause replication, acknowledge numbered writes on the primary, then fail it and compare the promoted replica against client receipts. Rebuild missing cache state from an authoritative ledger. In a separate Cluster test, move a slot while 29 clients update account-scoped counters; record MOVED and ASK handling and reconcile final values. A client error rate of zero is not enough if redirected retries apply an external effect twice.</p>"
    "<h2>Recover pending work and missed hints</h2><p>Commit a shipment projection effect, crash before stream acknowledgment, claim the idle pending entry, and show that the unique event receipt prevents a duplicate projection. Pause a second group and test the proposed trim boundary against its oldest required entry. Disconnect a keyspace-notification subscriber while 83 reservation keys expire. Run a bounded database reconciliation and prove all 83 reach their intended state. Retain screenshots or command output for each fault, the expected ledger, and the measured recovery time.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not infer durability from a successful write response alone.</li><li>Do not declare failover complete before clients and state reconcile.</li><li>Do not use a notification feed as the only record of an expiry-driven effect.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*related_paths, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Redis recovery boundaries drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What does an RDB file capture?", ["A point-in-time dataset", "Every write acknowledged after the snapshot", "A durable Pub/Sub offset"], "Writes after a snapshot need another recovery source."),
    ("What is the tradeoff of periodic AOF synchronization?", ["Recent acknowledged writes may be absent after a failure", "Every command is transactionally replicated", "Snapshots become unnecessary"], "Fsync cadence defines a possible recent-write gap."),
    ("What can noeviction do at the memory limit?", ["Reject writes needing more memory", "Evict the least recently used key", "Turn replicas into primaries"], "Reads may continue while writes fail."),
    ("Why separate session authority from an all-keys cache?", ["An evictable cache may remove a session token", "It makes every key share one TTL", "It disables persistence"], "Key meaning must match eviction behavior."),
    ("Can Sentinel promotion lose acknowledged writes?", ["Yes, asynchronous replication can leave a gap", "No, promotion is a transaction commit", "Only if every client is disconnected"], "Promotion and write durability are separate properties."),
    ("Does WAIT make Redis strongly consistent?", ["No; it reduces some replication risk but cannot guarantee all failovers", "Yes; every failover preserves every write", "Yes; it replaces disk persistence"], "Replica acknowledgment alone is not a complete strong-consistency protocol."),
    ("What must a Cluster client handle during resharding?", ["MOVED and ASK redirections", "Only DNS changes", "Only queue acknowledgments"], "Slot ownership can change while requests are in flight."),
    ("What cost can account hash tags create?", ["A hot slot that cannot be split without changing keys", "Automatic write durability", "A shorter AOF"], "Co-location also concentrates traffic."),
    ("What does a stream entry in the pending list mean?", ["Delivered but not acknowledged for that group", "Stored only in an RDB snapshot", "Confirmed by all groups"], "Pending work requires reconciliation before claiming or trimming."),
    ("A worker claims an idle stream entry. What must it check before an external effect?", ["A unique business event receipt", "Only the stream length", "Only a Pub/Sub channel"], "The previous owner may have committed the effect before crashing."),
    ("Can a keyspace notification subscriber replay events missed while disconnected?", ["No; Pub/Sub does not retain them", "Yes; reconnect starts at the previous offset", "Only after AOF rewrite"], "A durable authority and reconciliation path cover missed hints."),
    ("What should trigger an expiry-dependent financial release?", ["A conditional state transition from an authoritative ledger", "Only a keyspace event", "Only a cache TTL value"], "A notification can wake work but cannot be its sole correctness record."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on Redis persistence, eviction, Sentinel, Cluster, Streams, and notifications.",
            sort_order=26000, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in related_paths],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the Redis boundary that determines whether a write, cache miss, failover, stream delivery, or notification can be recovered. Keep the application effect separate from the in-memory data structure.</p>"
    "<h2>Review these lessons</h2>" + links(related_paths)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-rabbitmq-operating-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not count acknowledged writes as necessarily restored writes.</li><li>Do not treat a Pub/Sub subscriber as a durable consumer group.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Redis operating decisions</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for source, targets in {
    "devops/backup-and-recovery": [related_paths[0]],
    "devops/cache-stampede-control": [related_paths[1], related_paths[5]],
    "devops/failover-write-fencing": [related_paths[2]],
    "devops/retry-timeout-budgets": [related_paths[3]],
    "devops/dead-letter-replay": [related_paths[4]],
    "devops/scheduled-function-overlap-control": [related_paths[5]],
    "devops/kafka-consumer-offset-recovery": [related_paths[4], project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Redis operating follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1,
                  "total_records": len(rows)}))

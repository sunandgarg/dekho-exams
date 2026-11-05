"""Add RabbitMQ operating-boundary lessons, a drill, and a quiz."""

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
project_path = "devops/rabbitmq-delivery-recovery-project"
quiz_path = "quizzes/devops-rabbitmq-operating-decisions"


def lesson(slug, title, summary, definition, decision, sample, cost, mistakes, related):
    return dict(path="devops/" + slug, title=title, summary=summary,
                definition=definition, decision=decision, sample=sample,
                cost=cost, mistakes=mistakes, related=related)


specs = [
    lesson(
        "rabbitmq-routing-confirm-boundary",
        "RabbitMQ publishing: distinguish broker confirmation from queue routing",
        "A confirmed publish can still be unroutable unless the publisher checks the routing result.",
        "A RabbitMQ publisher sends a message to an exchange, which routes it to bound queues. Publisher confirms tell the client that the broker handled a publish under the queue's confirmation rules; they are not proof that an application consumer completed work. An AMQP 0-9-1 publish that matches no queue may be discarded when the mandatory flag is false and no alternate exchange handles it. With mandatory publishing, an unroutable message is returned to the publisher, which must register and act on the return. Reliable publishing therefore needs both a routing outcome and a confirm outcome, correlated with the original business event ID.",
        "An invoice service emits event inv-7284 to an exchange using routing key settlement.ready. A staging binding is accidentally renamed. The producer enables mandatory publishing, handles returned messages, and waits for confirms. It records the event as delivered only when the message was not returned and the broker confirmed it. If the channel closes before the confirm, the outcome is ambiguous: the service retries from its outbox with the same business ID, and the consumer deduplicates that ID. A confirm cannot replace the outbox transaction if database commit and publish are separate actions. The operator tests a removed binding and a lost connection before accepting the topology.",
        "Exchange: settlement-events\nRouting key: settlement.ready\nBusiness event: inv-7284\nmandatory: true; returned-message handler: required\nconfirmed + not returned: broker accepted route\nconnection lost before confirm: ambiguous, retry same business ID",
        "Confirm tracking consumes memory per unacknowledged publish and adds round-trip or batched waiting time. Large outstanding windows make reconnect recovery harder because more events have uncertain status. A returned message is a topology defect, not an ordinary transient retry target; alert on it with the exchange and routing key. Confirm rates and return rates should be observed together. Test the actual queue binding, not just a producer callback. Downstream processing still requires manual consumer acknowledgment and an idempotent effect ledger when duplicates would cause harm.",
        ["Do not interpret a publisher confirm as a consumer acknowledgment.", "Do not discard mandatory returns while recording the publish as delivered.", "Do not create a new business ID for an ambiguous retry."],
        ["devops/transactional-outbox-delivery", "devops/queue-consumer-reliability", "devops/event-schema-evolution"],
    ),
    lesson(
        "rabbitmq-quorum-queue-majority",
        "RabbitMQ quorum queues: plan node maintenance around majority availability",
        "A replicated queue cannot keep accepting state changes after it loses its majority.",
        "A RabbitMQ quorum queue stores its state on a leader and follower members using a majority agreement. Queue members, not the total count of cluster nodes, define that majority. In a three-member queue, two available members form a quorum; a second member loss leaves no majority for normal queue progress. Publisher confirms are the client's evidence that a published message was replicated according to the queue's safety boundary. Manual consumer acknowledgments protect messages that were delivered but not completed. Neither mechanism eliminates business-level duplicate processing after a connection break or an ambiguous acknowledgment.",
        "A three-node order cluster hosts a three-member quorum queue. Before taking broker B offline, the operator checks which nodes host members and whether the queue is healthy; a different queue could have a different membership set. During B maintenance, broker A fails unexpectedly, leaving one member available. Publishing and consumption for that queue become unavailable until majority is restored. The team does not delete the queue or force a replacement to clear an alert. It restores the missing member, waits for catch-up, verifies confirmed event IDs and consumer progress, and only then resumes further maintenance. Queue leader distribution is inspected too: one node carrying most leaders can become a throughput bottleneck.",
        "Queue: order-work\nMembers: broker-A, broker-B, broker-C\nMajority: 2 members\nMaintenance: stop broker-B only after health check\nUnexpected broker-A loss: 1 member remains; queue unavailable\nRecovery: restore member, verify catch-up, reconcile confirmed IDs",
        "Quorum replication costs disk, network traffic, and confirmation latency. Adding members increases fault tolerance only when placement and failure domains are real; copying a queue onto three processes on one host does not survive that host's loss. Hundreds of idle queues also consume metadata and supervision resources. Check member placement before draining a node, and record the exact member set after expansion or shrink operations. Use a disposable cluster to test one-node and two-node outages. A successful TCP connection to a surviving broker does not prove a particular queue still has quorum.",
        ["Do not count cluster nodes as if every queue has a member on each one.", "Do not perform overlapping maintenance that removes the queue's majority.", "Do not treat publisher confirms as proof of an external database effect."],
        ["devops/etcd-quorum-maintenance", "devops/queue-consumer-reliability", "devops/recovery-time-budget-ledger"],
    ),
    lesson(
        "rabbitmq-consumer-ack-prefetch",
        "RabbitMQ consumers: couple manual acknowledgments to a bounded prefetch window",
        "A consumer can exhaust memory before the broker's ready-message count looks alarming.",
        "RabbitMQ manual acknowledgments separate delivery from completion. A message remains unacknowledged until the consumer sends an acknowledgment on the channel that received its delivery; a closed channel can cause those outstanding deliveries to be offered again. Prefetch limits how many unacknowledged deliveries are sent ahead of completed work. Without an effective limit, a fast broker can fill consumer memory even when processing is slow. Prefetch is not a concurrency setting by itself: the worker's actual task limit, downstream capacity, and message size must agree with it. Delivery tags are scoped to a channel, so an acknowledgment on another channel is invalid.",
        "A document-indexing worker has eight execution slots, each using about 14 MiB of working memory. Start with prefetch near the execution-slot count and measure throughput, unacknowledged messages, resident memory, and downstream search pressure. After an index write and its unique document-event receipt commit, acknowledge on the original channel. If the write fails transiently, release the delivery through a bounded retry path rather than hot-looping immediate requeues. If a worker dies after indexing but before acknowledging, the same event can return; the unique receipt turns that delivery into a no-op. Verify this crash point explicitly in the fault drill.",
        "Worker slots: 8\nPer-task working set: about 14 MiB\nInitial prefetch target: 8, then measure\nEffect: index update + unique event receipt\nAcknowledgment: original delivery channel, after effect commit\nCrash after commit: redelivery rejected by receipt key",
        "A larger prefetch can improve throughput when processing is cheap and network latency dominates, but it also increases outstanding memory and redistributes work less fairly among consumers. A prefetch of zero can mean no limit under AMQP 0-9-1, so it should not be used to mean pause. Measure queue-ready, unacknowledged, consumer CPU, and processing age separately. A low ready count with a high unacknowledged count may indicate consumers holding work rather than finishing it. If completion takes longer than an acknowledgment timeout, increase capacity or redesign the work unit before simply extending the timeout.",
        ["Do not use automatic acknowledgment for work that must survive a consumer crash.", "Do not acknowledge a delivery on a different channel.", "Do not tune prefetch from ready-message count alone."],
        ["devops/queue-consumer-reliability", "devops/queue-age-scaling-contract", "devops/dead-letter-replay"],
    ),
    lesson(
        "rabbitmq-dead-letter-transfer",
        "RabbitMQ dead lettering: make poison-message transfer observable and recoverable",
        "Moving a failed message to another queue is a second routing operation with its own failure mode.",
        "RabbitMQ can dead-letter messages after a rejection without requeue, expiration, queue-length action, or a delivery-limit event, depending on queue type and policy. The source queue republishes to a dead-letter exchange; an absent binding or unavailable target can make the transfer unsafe under ordinary at-most-once behavior. Quorum queues offer an at-least-once dead-letter strategy when its required policy settings are present, including reject-publish overflow. That strategy retains source messages until target confirmation, but adds internal consumer work and can occupy source queue capacity. A dead-letter queue is useful only when its owner can diagnose, repair, and safely replay the event.",
        "A settlement decoder rejects a malformed event after a bounded number of attempts. The source quorum queue sends it to a durable quarantine queue through an explicitly bound dead-letter exchange; the original publish uses persistent delivery mode so the target can retain it through a restart. The operator injects a missing target binding and confirms that the source does not silently lose the event under the chosen strategy. They then restore the binding, check the transfer receipt, and replay after repairing the decoder. The replay tool preserves the original business event ID, records the reason and count of previous attempts, and throttles its publish rate. Rejecting every event immediately back to the same source would form an expensive redelivery loop instead of a repair workflow.",
        "Source: settlement-work quorum queue\nFailure: bounded delivery attempts exhausted\nDead-letter exchange: settlement-failures\nTarget: settlement-quarantine, durable and bound\nTransfer policy: at-least-once with reject-publish overflow\nReplay: preserve business ID and cap release rate",
        "At-least-once transfer uses additional CPU and memory and may retain dead letters in the source while the destination is blocked. A queue-length cap and overflow policy must be reviewed together; switching to drop-head can remove the transfer guarantee and strand an unconfirmed handoff. Monitor source depth, dead-letter consumer backlog, target confirms, and quarantine age. Before changing a live policy, rehearse a missing binding and target outage. Never assume a dead-letter exchange is a lossless archive merely because the queue name exists in a dashboard.",
        ["Do not send poison messages back to the same hot queue indefinitely.", "Do not call a dead-letter transfer safe without checking target routing and confirms.", "Do not switch overflow policy without reviewing the at-least-once transfer contract."],
        ["devops/dead-letter-replay", "devops/queue-visibility-lease", "devops/queue-consumer-reliability"],
    ),
    lesson(
        "rabbitmq-ttl-expiry-capacity",
        "RabbitMQ TTL: separate message expiry from immediate storage reclamation",
        "Expired messages can still occupy broker resources until they reach a cleanup point.",
        "RabbitMQ message time-to-live limits how long a message is eligible for delivery while it waits in a queue. It is different from queue TTL, which governs removal of an unused queue. Expired messages are not necessarily reclaimed at the precise expiry timestamp: messages can wait behind older records, and queue-type behavior affects when they are discarded or dead-lettered. A message can also be delivered around its expiry boundary, so TTL is not a substitute for an application-side deadline check before charging a card or sending a time-sensitive notification. Storage limits, dead-letter routes, and consumer capacity must be planned together.",
        "A delivery-notification queue holds time-sensitive updates for at most 47 minutes. The worker checks the event's business deadline again before sending because a message already in flight can become stale. The operator pauses consumers, publishes 700 messages with varied expiry times, and watches ready depth and disk bytes after the first messages expire. A dead-letter route sends expired records to an inspection queue only if there is a real review need; otherwise retaining every expired notification can create a second backlog. A replay tool must not send an expired command as if it were new work. It records the original deadline and requires an explicit replacement request.",
        "Message wait TTL: 47 minutes\nBusiness deadline: checked at effect time\nPaused-consumer test: 700 synthetic messages\nObserve: ready depth, disk bytes, expired/dead-letter counts\nExpired command replay: reject without a new business request",
        "Short TTL reduces stale work but can drop legitimate messages during a temporary consumer outage. Long TTL preserves more work but increases storage and recovery cost. Neither choice guarantees instant disk release: segment and queue cleanup behavior can delay reclamation. Test expiry under a paused consumer and a large queue, not only on an empty local queue. Alert on oldest eligible work and on expired-message counts. When applying TTL retroactively, observe the actual drain and cleanup path before using it as an emergency disk-pressure control.",
        ["Do not confuse message TTL with queue TTL.", "Do not use TTL as the only business-deadline check.", "Do not promise that expired messages free disk exactly at the expiry timestamp."],
        ["devops/queue-age-scaling-contract", "devops/dead-letter-replay", "devops/cost-capacity-ownership"],
    ),
    lesson(
        "rabbitmq-queue-policy-migration",
        "RabbitMQ queue policies: migrate immutable queue type without losing the handoff",
        "A policy update can change runtime limits, but it cannot turn an existing classic queue into a quorum queue.",
        "RabbitMQ policies apply selected queue and exchange settings at runtime, including dead-letter routing, TTL, and length limits. Queue type is fixed when the queue is declared; changing a matching policy does not convert a classic queue into a quorum queue. Some client-declared arguments also conflict with policy changes because declaration equivalence is checked when a queue already exists. A queue-type migration is therefore an application and topology cutover, not a single control-plane edit. The cutover must account for messages already in the old queue, publishers in flight, consumers with unacknowledged deliveries, and the binding that defines future routing.",
        "A report worker moves from a classic queue to a quorum queue named report-work-v2. The team declares the new queue and bindings, confirms the new publish path in a shadow environment, then fences the old publisher route at a recorded event boundary. Old consumers drain remaining work while new consumers process only v2 messages. Unique report-request IDs prevent duplicate side effects if a publisher retries during the fence. The operator compares accepted publish receipts, old and new queue depths, unacknowledged counts, and completed report IDs before retiring the old queue. Rollback means restoring the old route with an explicit deduplication rule, not deleting v2 while it still holds work.",
        "Old queue: report-work (classic)\nNew queue: report-work-v2 (quorum)\nCutover marker: event ID report-48271\nFence old route; confirm new binding and publish receipts\nDrain old consumers; reconcile completed request IDs\nRetire old queue only after ready and unacknowledged reach zero",
        "Running two queues temporarily costs memory, disk, broker CPU, and more complex dashboards. A duplicate routing interval can make both queues receive the same request; a gap can lose new requests. Use one observable routing boundary and an application-level event ID to reconcile either case. Policy updates should be reviewed for scope, priority, and unintended queues matching the rule. Test rollback before the cutover, including how to drain work from v2. Do not hide topology drift by changing producers to tolerate conflicting declarations silently.",
        ["Do not expect a policy to mutate an existing queue's type.", "Do not delete an old queue merely because its ready count is zero while deliveries remain unacknowledged.", "Do not run a dual-route cutover without a duplicate-effect guard."],
        ["devops/gitops-resource-ownership-transfer", "devops/queue-consumer-reliability", "devops/release-evidence-record"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_path] = "RabbitMQ delivery recovery project: confirms, quorum, and queue cutover"
titles[quiz_path] = "RabbitMQ operating decisions: routing, recovery, and queue policy quiz"
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
    ("RabbitMQ publish and consume safety", "Separate routing, broker replication, and completed consumer effects.", related_paths[:3]),
    ("RabbitMQ failure and migration", "Repair poison messages, bound expiry, and migrate queue policy safely.", related_paths[3:]),
]:
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "rabbitmq", "queue-operations"],
               sort_order=25710 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Rehearse unroutable publishes, quorum loss, consumer crash, dead-letter failure, expiry, and queue-type cutover.",
               difficulty="Advanced", sort_order=25790,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 12,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related_paths]}
project["body"] = (
    "<p>Use an isolated three-node RabbitMQ cluster and synthetic report requests. Declare a quorum work queue, a quarantine queue, and their exchange bindings. Give each request a stable business ID and keep an external expected-ID ledger. Enable publisher confirms, mandatory returns, and manual consumer acknowledgments. The exercise passes only when accepted publish IDs match the durable work or completed-effect ledger after each fault; a green connection indicator alone is insufficient.</p>"
    "<h2>Prove publish and consume boundaries</h2><p>Remove a binding and publish 73 synthetic requests; verify mandatory returns are handled and none are falsely marked delivered. Restore the binding, publish again, and kill the producer before its last confirm arrives. Retry ambiguous IDs and confirm that the consumer effect ledger rejects duplicate report generation. Set bounded prefetch near actual worker slots. Crash a worker after it records a completed report but before it acknowledges, then show that redelivery does not create a second report. Capture ready and unacknowledged depth separately.</p>"
    "<pre><code class=\"language-text\">Acceptance ledger\nRequested report IDs: 73\nUnroutable test: 73 returned, 0 marked delivered\nAfter binding repair: accepted IDs match queue or completed ledger\nProducer lost-confirm retry: no duplicate report effect\nWorker crash after effect: redelivery guarded by business ID\nTwo quorum members lost: queue unavailable until majority restored</code></pre>"
    "<h2>Inject broker and dead-letter faults</h2><p>Stop one queue member, verify progress, then stop a second and record the failed operation. Restore the majority and reconcile confirmed publish IDs. Reject a poison event through a bounded delivery path. Remove the dead-letter target binding and measure source retention under the selected transfer strategy; repair the binding and inspect the quarantine receipt. Publish messages with a short TTL behind a paused consumer and compare expiry counters with actual disk use. Ensure the worker rejects a business deadline that has passed even when delivery occurs near expiry.</p>"
    "<h2>Cut over queue type</h2><p>Declare a second queue with the intended type and bindings. Fence the old publisher route at a recorded event ID, drain old deliveries, and start the new route. Reconcile source receipts, both queue depths, unacknowledged counts, and completed request IDs. Test rollback while the new queue still contains work. Preserve the commands, expected ledger, observed faults, and repair decisions; do not execute the exercise against production credentials.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not count confirms without checking unroutable returns.</li><li>Do not delete a queue with unacknowledged work.</li><li>Do not change dead-letter overflow without testing the transfer contract.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*related_paths, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>RabbitMQ delivery recovery drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("A publish is confirmed but matched no queue. Which signal reveals the routing failure?", ["A mandatory return handled by the publisher", "A consumer acknowledgment", "A lower prefetch count"], "Broker confirmation and routing outcome must both be considered."),
    ("A channel closes before a publish confirm arrives. What should the publisher assume?", ["The outcome is ambiguous and the same business ID may need retry", "The broker definitely discarded it", "The consumer definitely completed it"], "The missing confirm does not settle the publish outcome."),
    ("A three-member quorum queue loses two members. What remains?", ["No majority for normal queue progress", "A healthy two-member majority", "Automatic conversion to a classic queue"], "The queue's member set defines the majority."),
    ("Why use manual consumer acknowledgments?", ["To keep incomplete deliveries eligible for recovery", "To confirm the publisher's exchange route", "To change queue type"], "Completion and delivery must be separated for crash recovery."),
    ("What limits the worker's unacknowledged delivery window?", ["A measured prefetch setting", "The routing key length", "The exchange type alone"], "Bound the work sent ahead of completion."),
    ("Where must an AMQP delivery be acknowledged?", ["On the channel that received its delivery tag", "On any open channel", "Only on the publisher's channel"], "Delivery tags are scoped to their channel."),
    ("What can immediate requeue of a permanent poison message cause?", ["A costly redelivery loop", "Automatic schema repair", "Publisher routing verification"], "Bound attempts and send repairable failures to a controlled path."),
    ("Which overflow mode is required for the described quorum at-least-once dead-letter strategy?", ["Reject-publish", "Drop-head", "No acknowledgment"], "Changing to drop-head removes that transfer contract."),
    ("Does message TTL guarantee immediate disk release at expiry?", ["No; cleanup can wait for queue progress", "Yes, every expired byte is freed instantly", "Only if prefetch is unlimited"], "Expiration and storage reclamation are different events."),
    ("What else should a worker check before a time-sensitive effect?", ["The business deadline", "Only queue TTL", "Only the exchange name"], "A delivered message can be stale by the time an effect begins."),
    ("Can a policy turn an existing classic queue into a quorum queue?", ["No; queue type is fixed at declaration", "Yes; after one policy refresh", "Yes; when consumers stop"], "A queue-type change requires an explicit migration."),
    ("Which evidence proves a queue cutover was complete?", ["Publish receipts, both depths, unacknowledged work, and completed business IDs", "Only a zero ready count on the old queue", "Only a successful new declaration"], "Cutover needs a complete work and effect reconciliation."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on RabbitMQ routing, confirms, quorum, acknowledgments, dead lettering, TTL, and cutover.",
            sort_order=25800, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in related_paths],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the evidence that proves each RabbitMQ handoff. The broker accepting a publish, a queue holding it, and a consumer finishing an effect are separate events.</p>"
    "<h2>Review these lessons</h2>" + links(related_paths)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-kafka-operating-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not treat a publish confirm as a downstream effect receipt.</li><li>Do not treat a ready count of zero as proof that no work remains.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>RabbitMQ operating decisions</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for source, targets in {
    "devops/transactional-outbox-delivery": [related_paths[0]],
    "devops/queue-consumer-reliability": [related_paths[1], related_paths[2]],
    "devops/dead-letter-replay": [related_paths[3], project_path],
    "devops/queue-age-scaling-contract": [related_paths[4]],
    "devops/gitops-resource-ownership-transfer": [related_paths[5]],
    "devops/kafka-acks-isr-durability": [related_paths[1]],
}.items():
    row = by_path[source]
    row["body"] += "<h2>RabbitMQ operating follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1,
                  "total_records": len(rows)}))

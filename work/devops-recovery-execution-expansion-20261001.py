"""Add end-to-end disaster-recovery execution lessons to the local preview."""

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


def lesson(slug, title, summary, definition, operation, sample, cost, mistakes, related):
    path = "devops/" + slug
    assert path not in by_path, path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      operation=operation, sample=sample, cost=cost,
                      mistakes=mistakes, related=related))


lesson(
    "recovery-time-budget-ledger",
    "Recovery-time budgets: measure every stage of service return",
    "An RTO is met when the agreed user journey works again, not when a standby starts.",
    "A recovery-time objective bounds the elapsed time between a defined incident start and a defined service-restored condition. Split that interval into detection, declaration, fencing, data promotion, capacity, traffic movement, and user-path verification. The stages may overlap, but record actual timestamps and dependencies rather than adding guessed durations. A database responding to a local probe is only one checkpoint; an API that still cannot authenticate or settle a payment has not met its workload RTO.",
    "A claims-submission service declares a regional outage at 09:14. Its recovery record captures the last known successful customer submission, alert timestamp, human decision, primary-write fence confirmation, standby replay point, promotion, application readiness, first successful synthetic claim, and restoration of full intake. The team chooses the first successful end-to-end claim as the recovery endpoint and records degraded throughput separately. During a rehearsal, authentication depends on a regional key service that was omitted from the original timeline; the team adds that dependency and its alternate-region readiness check. Measure the critical path, not just the sum of every task, because capacity scaling can proceed while the write fence is established. Do not reset the stopwatch when a new incident commander takes over. If the recovery objective is missed, retain the measured interval and the stage that consumed the budget. Repeated drills reveal whether detection, operator decision, provisioning, replica catch-up, or traffic convergence is the binding delay. State the acceptance journey before the drill so the result cannot be redefined after a slow recovery.",
    "Claims recovery clock\nStart: last confirmed healthy customer claim at 09:14\nDeclare: incident decision recorded\nFence: former primary rejects writes\nData: selected standby replay point recorded\nReady: application and dependencies pass checks\nTraffic: customer endpoint routes to standby\nEnd: new claim accepted and queryable\nSeparate: time to full planned throughput",
    "Capturing T stage events is O(T) in record size and small beside the recovery itself. Parallel work shortens wall time only when it does not violate ordering: traffic must not reach an unfenced second writer. Measure p50 and worst rehearsed recovery times, stage variance, stale timestamps, and customer-path failures after a nominally successful promotion. Reserve time for verification and a retry instead of allocating every minute to provisioning.",
    ["Do not stop the clock when only the database is writable.", "Do not sum overlapping stage durations as if they were sequential.", "Do not change the accepted recovery endpoint after seeing the drill result."],
    ["devops/backup-and-recovery", "devops/multi-region-failover", "devops/incident-response", "devops/release-evidence-record"],
)

lesson(
    "standby-admission-checklist",
    "Standby admission: prove the recovery region can accept real work",
    "A standby is admissible only when its data, dependencies, permissions, and capacity support the recovery journey.",
    "A green health endpoint can hide an empty image registry, an expired certificate, a missing signing key, a quota ceiling, or a database replica too far behind the agreed data-loss bound. Admission is a pre-cutover decision: test the dependency graph and identify which checks are hard gates, which allow degraded service, and who may accept a bounded exception. Record actual values at decision time because a readiness result from yesterday does not describe the current outage.",
    "A shipment-tracking platform keeps a reduced-size standby. Before any traffic move, verify the deployment digest is pullable from a clean node, the alternate-region secrets and certificates decrypt, the database is on the expected timeline, queue consumers are paused or scoped, and image, compute, database, IP, and load-balancer quotas can cover a measured intake rate. Compare the projected rate with requests and autoscaling limits; a warm standby that serves one test request may still collapse under the first peak. Test outbound dependencies such as tax calculation and email by making a scoped synthetic request, while preventing the probe from sending real messages. A key needed to decrypt retained backups receives a separate gate from the key used by current traffic. If one nonessential analytics pipeline is absent, publish the resulting service mode and duration; if order writes cannot be fenced, block promotion. The admission sheet records owner, evidence time, observed value, threshold, decision, and a link to the repair action. Re-run the checks after scaling because new nodes may require a registry path and credentials the original warm nodes already cached.",
    "Shipment standby admission\nArtifact: tested digest pulls on clean node\nData: replay point inside accepted loss window\nWrites: old primary fenced; new epoch available\nIdentity: service tokens and certificates valid\nKeys: current data and retained restore points decrypt\nCapacity: quota plus measured intake headroom\nQueues: producer and consumer ownership defined\nDecision: hard gate, degraded mode, or block",
    "A full rehearsal costs a clean-node pull, scoped dependency probes, and capacity tests; those checks consume traffic and provider quota, so run destructive or costly probes in a disposable environment. With D dependencies, the admission inventory is O(D), but the slowest critical dependency may dominate time to readiness. Track failed gates, stale evidence age, first-hour saturation, and clean-node pull success instead of counting only green health endpoints.",
    ["Do not accept a standby from a single HTTP health response.", "Do not count cached images or credentials as proof a new node can start.", "Do not promote when the old writer may still accept transactions."],
    ["devops/provider-quota-preflight", "devops/node-autoscaling-headroom", "devops/registry-replica-promotion", "devops/encryption-key-rotation-recovery"],
)

lesson(
    "disaster-declaration-stop-conditions",
    "Disaster declaration: define authority, scope, and stop conditions",
    "A failover decision is an explicit change in service authority, not an automatic reaction to one red graph.",
    "The declaration contract names the impairment, affected user journey, recovery objective, evidence of standby readiness, expected data gap, and person authorized to move write authority. A partition can make two regions disagree about which side is healthy; an automated traffic switch without write fencing may create competing histories. A drill also needs stop conditions based on user impact, data integrity, and loss of rollback capability, with a separate procedure for halting fault injection and restoring protection.",
    "A document-signing service loses requests from one network path while its primary database is still healthy. The incident lead checks independent client probes and origin telemetry before declaring a regional disaster. A local routing repair may be faster and less risky than promoting a replica. For an exercise, the team limits the target to a disposable tenant, chooses a maximum synthetic error rate, records who can stop the experiment, and verifies that the stop mechanism works from outside the impaired region. A stop alarm can end fault injection, but it does not automatically undo every side effect or restore a deleted resource; the runbook includes explicit cleanup and validation. If the write-fence result is unknown, freeze the promotion step even if the response-time target is threatened. If the standby is admissible and the primary impairment meets the declared threshold, the authorized operator records the chosen epoch and initiates the reviewed sequence. Another operator independently checks the target and intended direction. The team separates the decision to fail over from the automation that performs the well-tested steps, so an ambiguous signal can be examined without hand-editing infrastructure in panic.",
    "Document-signing declaration\nImpact: named customer journey and measured failure\nDecision: repair locally or activate standby\nAuthority: incident lead plus independent checker\nHard stop: write fence unconfirmed or data gap exceeds bound\nExercise stop: synthetic error or integrity threshold crossed\nStop action: halt injection, inspect residual effects\nRecord: time, evidence, selected epoch, operator",
    "Decision gates add human minutes, but unbounded automatic promotion can add a much larger reconciliation cost. Record decision latency and false declarations alongside missed recovery objectives. For each exercise, account for probe volume, injected fault duration, cleanup time, and whether alarms and stop paths remained available during the simulated impairment. Practice the same authority path often enough that escalation is predictable.",
    ["Do not let one failing regional probe declare the entire region lost.", "Do not assume stopping a fault experiment reverses its side effects.", "Do not let the person choosing the target also be the only person verifying it."],
    ["devops/incident-response", "devops/failover-write-fencing", "devops/dns-cutover-safety", "devops/multi-region-failover"],
)

lesson(
    "failover-ordering-control-points",
    "Failover ordering: fence, promote, validate, then move clients",
    "A recovery sequence must establish a single accepted writer before it directs new writes to the standby.",
    "Traffic and write authority are separate control planes. A DNS change can steer some clients while others retain old connections; a replica promotion can create a new database timeline while old application workers continue using the former primary. A safe sequence gives each transition a measurable gate: stop or fence old writers, select a recoverable replay point, promote once, test the new writer, then route clients and verify outcomes. A provider-specific failover system may implement parts atomically, but the application still needs evidence of the resulting authority.",
    "A reservation API uses an epoch stored outside the impaired database to decide which region may commit. The operator advances that epoch and tests that an old-region worker with the previous token is rejected. The standby's replay position is recorded before promotion; once promoted, a synthetic reservation is written and read back through the new application stack. Only then does the traffic controller favor the standby endpoint. Existing clients may keep old TCP connections or cached DNS answers, so the old region remains fenced and returns a retryable response rather than accepting writes. Watch client error rate, new-region commit rate, and old-region rejected-write count during convergence. If promotion succeeds but edge routing stalls, keep the new writer authoritative and repair routing; do not reopen the old writer to meet a dashboard target. If a probe write cannot be isolated from customer inventory, use a dedicated test tenant and delete it only after retention requirements are checked. Save the exact control-plane operation results and application observations, since a command returning success is weaker evidence than a rejected stale writer and a successful customer-path transaction.",
    "Reservation failover gates\n1. Freeze or fence old write authority\n2. Record chosen standby replay position\n3. Promote one standby and record new epoch\n4. Write/read synthetic reservation through app\n5. Shift traffic while old endpoint stays fenced\n6. Verify old-token rejection and user-path success",
    "Each gate adds at least one round trip; the dominant cost is usually replication catch-up, provisioning, and client convergence, not checking the epoch. The system temporarily consumes capacity in both regions. Track rejected stale writes, commits by region and epoch, promotion retries, traffic convergence, and end-to-end transaction success. Never optimize seconds out of the sequence by allowing two writers to overlap without a proven conflict protocol.",
    ["Do not treat DNS movement as proof the old writer is disabled.", "Do not retry promotion blindly after an ambiguous timeout.", "Do not send customer writes to the standby before a real application-path check."],
    ["devops/failover-write-fencing", "devops/lease-leadership-fencing", "devops/dns-negative-cache-cutover", "devops/pitr-timeline-acceptance"],
)

lesson(
    "recovery-write-gap-ledger",
    "Write-gap ledgers: account for acknowledged work that never reached the standby",
    "An asynchronous replica can be internally consistent and still lack customer writes that the former primary acknowledged.",
    "The recovery-point objective is a business loss bound, not simply a replication-lag metric. Compare the last durable primary acknowledgement with the selected standby replay point and account for writes in API logs, idempotency records, transactional outboxes, queues, external payment systems, and object stores. Those systems may have different replication boundaries. Missing and duplicate work require different actions: reconcile absent accepted requests, while deduplicating retries that arrive after the client lost its response.",
    "A payout service fails after acknowledging transfers numbered 641 through 648. The standby contains records through 645. The operator freezes new disbursements and creates a ledger with each request ID, client acknowledgement, database commit position, outbox event, queue delivery, and bank-provider reference. Requests 646 and 647 reached the provider but not the standby, so replaying them as new transfers would double-pay; reconstruct them using provider IDs and the original idempotency keys. Request 648 has a client acknowledgement but no provider receipt, so it needs a bounded investigation and customer-facing state, not a guessed success. A queue in the lost region might retain undelivered messages when service returns; keep its consumers paused until ownership and deduplication rules are set. Record the earliest unrecoverable acknowledgement and compare its time with the declared data-loss budget. A zero-byte replica lag reading after promotion says nothing about writes that never arrived. Have finance or the domain owner sign off the disposition of each uncertain transfer before normal automation resumes.",
    "Payout write-gap record\nRequest: 646\nClient: acknowledged\nStandby: absent at selected replay point\nOutbox: present only in old region\nProvider: accepted with stable reference\nAction: reconstruct local state; never resubmit payment\nOwner: payout operations\nStatus: pending independent reconciliation",
    "The ledger needs O(W) review for W writes in the uncertainty window; indexed request IDs and provider references reduce search cost but do not remove domain review. Retain raw evidence long enough to resolve disputes, while restricting sensitive financial fields. Measure unresolved acknowledgements, duplicate-provider submissions, outbox gaps, reconciliation age, and the actual time between last accepted primary write and standby recovery point.",
    ["Do not equate low replica lag with zero lost acknowledged writes.", "Do not replay a transfer until external side effects are checked.", "Do not restart old-region consumers before queue ownership is settled."],
    ["devops/replica-lag-read-contract", "devops/transactional-outbox-delivery", "devops/http-idempotency-replay", "devops/dead-letter-replay"],
)

lesson(
    "cutover-connection-drain-contract",
    "Cutover drains: handle old connections and ambiguous client retries",
    "Traffic cutover is a period of mixed client behavior, even after the routing control reports a new destination.",
    "DNS caches, persistent HTTP connections, proxy pools, mobile clients, and queued jobs do not all change endpoint at once. A drain contract defines which requests can finish on the old region, which receive a retryable refusal, how long an old connection may persist, and how a repeated operation is identified. The old region must keep enforcing the new write epoch throughout convergence; draining without fencing leaves a narrow but real second-writer window.",
    "A parcel-label API routes new sessions to a standby while old mobile clients keep established connections. Read-only label lookups can complete on the old endpoint if their staleness bound is acceptable. Label purchases require the current write epoch; a stale connection receives a retryable response with no side effect. Clients reuse the original purchase idempotency key when retrying against the standby. Instrument requests by region, operation, client connection age, epoch, and outcome, then wait for the old-region in-flight count to reach the agreed drain threshold. Do not kill every old connection immediately: an abrupt close during a response can make clients uncertain whether a purchase committed. Also do not wait forever for one idle client; enforce a maximum age and a safe retry path. Test a request that commits just before connection loss and a request rejected just after epoch change. Both must have a discoverable final state. If a background worker uses a private endpoint that bypasses public routing, include it in the drain inventory and keep it fenced until its owner confirms the new destination.",
    "Parcel cutover matrix\nOld read: serve only within staleness contract\nOld write with stale epoch: reject without side effect\nNew write: accept with stable idempotency key\nAmbiguous response: query by request ID, then retry\nPrivate worker: switch endpoint and verify epoch\nDrain complete: old in-flight below threshold",
    "Connection age and in-flight counts require per-region metrics and enough cardinality control to avoid exploding telemetry cost. A long drain holds capacity and certificates in two places; a short drain increases retries and ambiguous outcomes. Measure successful customer operations, duplicate purchase attempts, old-region rejected writes, connection age, and time until the last old write-capable path is closed.",
    ["Do not assume a routing-control change closes existing connections.", "Do not generate a new idempotency key on every retry.", "Do not forget private workers that bypass the public hostname."],
    ["devops/dns-cutover-safety", "devops/http-idempotency-replay", "devops/circuit-breaker-recovery-probes", "devops/failover-write-fencing"],
)

lesson(
    "failback-timeline-reconciliation",
    "Failback: rebuild the former primary before returning write authority",
    "Failback is another controlled migration, because a recovered primary may have a data history that diverged from the promoted writer.",
    "When a standby is promoted, it starts an authoritative history. The former primary may contain transactions that never replicated, and it must not be reconnected as a writer merely because its process starts. Preserve it for evidence, fence it, reconcile any unique accepted work, then rebuild or rewind it into a follower of the promoted system using a procedure supported by the database and its timeline requirements. Treat the return traffic move as a fresh cutover with its own data and capacity gates.",
    "A booking service now writes in the recovery region. The former primary comes back with three local bookings beyond the last replicated position. Keep its network path to clients blocked, take a forensic copy, and compare those bookings with payment and notification records. Reconcile each customer outcome in the current writer before the old node is resynchronized. If a database rewind tool is used, first verify that the two clusters share the expected history and required logs; if they do not, provision a fresh replica from a known-good base backup instead. Follow the new writer until lag is within the planned bound, test application reads and a controlled write in the current region, and confirm the returning region rejects writes before any return cutover. A return can wait until ordinary business hours if the recovery region has enough capacity and protection. Do not perform it solely to restore geography while the new region is still serving correctly. After the eventual return, reverse replication again and verify that a standby exists; otherwise the service has silently lost its next recovery path.",
    "Booking failback gates\nFormer primary: fenced and copied for investigation\nUnique writes: reconciled with customer outcomes\nResync: rewind validated or fresh replica created\nCatch-up: timeline and lag checked\nReturn: new epoch, application probe, traffic drain\nProtection: standby replication restored afterward",
    "Resynchronization can consume database I/O, network bandwidth, retained logs, and hours of operator time; a full rebuild may cost more but avoids an unsafe rewind across incompatible histories. Track unreconciled unique writes, replica lag, customer-path success, old-writer rejection, and days spent without a healthy standby. The recovery region's temporary capacity cost is often smaller than the cost of a rushed second outage.",
    ["Do not restart the former primary as a writer on process recovery.", "Do not discard its unique writes before domain reconciliation.", "Do not declare failback finished without rebuilding a standby."],
    ["devops/pitr-timeline-acceptance", "devops/failover-write-fencing", "devops/multi-region-failover", "devops/data-continuity-recovery-project"],
)

lesson(
    "recovery-drill-evidence-reset",
    "Recovery drills: retain evidence and reset the next line of defense",
    "A rehearsal is complete only when its measured result is recorded and the service is protected for another failure.",
    "The evidence package links a declared scenario to the actual user-path result, timestamps, data gap, operator decisions, artifacts, and stop-condition behavior. It distinguishes a tabletop, a synthetic fault in an isolated environment, and a production rotation; passing one does not prove the others. Reset includes restoring standby replication, backups, routing controls, credentials, alerts, capacity, and queue ownership. A drill that leaves the standby stale has improved confidence on paper while reducing real recovery readiness.",
    "A catalog-search team runs a scoped region-rotation drill for a disposable tenant. The recorder captures start and end markers from an external probe, one successful catalog update, a rejected stale-region update, replica replay positions, DNS and connection observations, capacity peak, and every manual override. A stop threshold fires when synthetic checkout errors exceed the agreed bound; the team halts fault injection, checks residual effects, and records whether the stop occurred before or after customer-path impact. It then reverses the exercise with a separately reviewed failback sequence, re-establishes replication, verifies a recent restorable backup and key access, restores old routing-control defaults, and checks alerts in both regions. The report labels untested paths, such as a full provider-region loss, instead of extending a narrow drill result to them. Findings become owned actions with deadlines and a repeat-test condition. The next drill uses a changed assumption, such as a clean node with no cached image, to reveal a different dependency rather than replaying the same happy path indefinitely.",
    "Catalog recovery evidence\nScenario and blast radius recorded\nExternal user-path start/end timestamps retained\nOld-writer rejection and new-writer success observed\nReplay point and actual data gap captured\nStop threshold and residual effects inspected\nFailback and standby protection restored\nOpen findings have owner and repeat-test condition",
    "Evidence collection is O(E) for E events and artifacts, while running two regions and restoring copies drives the real cost. Retention should be long enough to compare drills and incident outcomes without keeping sensitive payloads unnecessarily. Measure how often the drill meets its declared recovery targets, how long protection remains degraded afterward, repeat findings, and whether action owners actually close their gaps before the next exercise.",
    ["Do not call a tabletop exercise proof of live failover timing.", "Do not stop recording at first successful request while protection remains degraded.", "Do not leave routing controls or replication in their temporary drill state."],
    ["devops/incident-review-actions", "devops/release-evidence-record", "devops/backup-and-recovery", "devops/failback-timeline-reconciliation"],
)


titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/recovery-execution-drill-project"
quiz_path = "quizzes/devops-recovery-execution-decisions"
titles[project_path] = "Project: rehearse a fenced regional recovery and failback"
titles[quiz_path] = "DevOps recovery execution decisions"
assert all(path in titles for item in specs for path in item["related"])
assert project_path not in by_path and quiz_path not in by_path


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, slugs in [
    ("Recovery clock and standby gates", "Time the user journey and verify that the standby can serve it.", ["recovery-time-budget-ledger", "standby-admission-checklist"]),
    ("Declaration and ordered promotion", "Give operators an authority path and fence writes before routing changes.", ["disaster-declaration-stop-conditions", "failover-ordering-control-points"]),
    ("Lost work and mixed clients", "Reconcile acknowledged work and handle old connections during cutover.", ["recovery-write-gap-ledger", "cutover-connection-drain-contract"]),
    ("Failback and evidence", "Rejoin the former primary safely and reset recovery protection after a drill.", ["failback-timeline-reconciliation", "recovery-drill-evidence-reset"]),
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
               category="DevOps", difficulty="Advanced", tags=["devops", "disaster-recovery"],
               sort_order=22400 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['operation'])}</p>"
        f'<pre><code class="language-text">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]])
    )
    rows.append(row)

project_related = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Measure a full recovery clock, reconcile uncertain writes, and restore standby protection.",
               difficulty="Advanced", sort_order=22490,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 10,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Run this drill in two disposable environments with a synthetic reservation service, a database replica, a queue, and a client probe outside both regions. Use a small preloaded dataset and a stable request identifier for each reservation. The exercise passes only when a customer-path reservation works in the recovery region, the former writer rejects new commits, uncertain acknowledgements are reconciled, and a protected standby exists after failback.</p>"
    "<h2>Declare the scenario and budget</h2><p>Set a workload RTO and RPO before starting. Define the recovery clock's start and end events, maximum synthetic error rate, stop operator, allowed tenant, and hard block for an unconfirmed write fence. Capture external-probe timestamps rather than relying on clocks inside the impaired region. Prove the standby can pull the tested image on a clean node, decrypt required secrets, connect to its dependencies, and scale within quota. Fail one admission gate deliberately and show that the operator refuses promotion until it is repaired or an approved degraded mode is recorded.</p>"
    "<h2>Inject failure and move authority</h2><p>Write several reservations near the fault boundary; arrange for one acknowledged request to be absent from the standby and one client response to be lost after commit. Keep their identifiers and external side effects observable. Fence the primary using a monotonic epoch or an equivalent enforced mechanism, then prove a stale worker cannot write. Record the standby replay point. Promote one standby, run a synthetic write/read through the application, and shift new traffic. Keep old connections alive long enough to test stale-write refusal and same-key retries. If the promotion command times out, inspect actual state before trying again.</p>"
    "<pre><code class=\"language-text\">Recovery drill acceptance\nRTO start and end are external customer-path events\nStandby admission includes clean-node pull and capacity\nOld writer rejects an outdated epoch before traffic moves\nPromoted writer accepts one isolated synthetic reservation\nUncertain requests have acknowledgement and side-effect status\nOld connections cannot create a second committed reservation\nFormer primary follows the promoted history before return\nBackup, replica, alerts, and routing controls reset after drill</code></pre>"
    "<h2>Reconcile and fail back</h2><p>Build a per-request write-gap ledger from client acknowledgements, database positions, queue deliveries, and any external provider IDs. Do not replay an ambiguous operation until its original side effect is known. Bring the former primary back only behind a write fence, preserve a copy for investigation, and either resynchronize it to the promoted timeline or rebuild it from a clean base. Test replication catch-up and a second application-path cutover. Restore a standby in the opposite direction, verify recent backup readability and key access, and check that alerting and routing controls have returned to their intended state.</p>"
    "<h2>Report the result</h2><p>Report elapsed time by stage, actual data gap, customer errors during convergence, old-region rejected writes, peak standby saturation, stop-condition behavior, manual overrides, and time spent without a healthy standby. Label environment-specific results as such: a local simulation does not establish provider-region behavior or production throughput. Assign an owner and repeat-test condition to every failed gate. A repeat drill should remove one hidden dependency, such as cached image layers or a preexisting connection.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not switch traffic while two writers can commit.</li><li>Do not replay a transaction with unknown external side effects.</li><li>Do not leave the former primary writable or the new region without a standby.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Fenced recovery execution drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("When should the recovery clock stop?", ["At the predefined successful customer journey", "When a database process starts", "When an operator opens a dashboard"], "RTO requires a user-visible service endpoint defined before the drill."),
    ("What makes a warm standby admissible?", ["Current data, dependencies, credentials, and capacity pass named gates", "One cached health response", "A replica resource exists"], "Readiness covers the full application path."),
    ("What blocks promotion even if the RTO is tight?", ["The former writer may still accept commits", "A nonessential report is delayed", "One synthetic client uses a cached address"], "Unfenced promotion risks divergent write histories."),
    ("Why record the standby replay point before promotion?", ["It bounds which primary writes the standby received", "It changes DNS TTL", "It clears a queue automatically"], "The replay point is evidence for the data gap."),
    ("What should follow an ambiguous promotion timeout?", ["Inspect the actual writer state before another attempt", "Promote a second replica immediately", "Open writes on both regions"], "The first command may already have succeeded."),
    ("What does a zero lag reading after failover fail to prove?", ["That every acknowledged primary write reached the standby", "That the new process accepts reads", "That traffic has moved"], "Missing writes can sit beyond the selected replay point."),
    ("How should an ambiguous payment retry be handled?", ["Check the original side effect and reuse its idempotency identity", "Create a fresh payment identifier", "Assume no external provider accepted it"], "A lost response does not prove the side effect failed."),
    ("Why can old clients still matter after routing changes?", ["Cached DNS and persistent connections may keep using the old endpoint", "A routing update deletes all sockets", "Only new clients can write"], "The old endpoint must remain fenced through convergence."),
    ("How should the former primary return after promotion?", ["Fenced, reconciled, and rebuilt or rewound as a follower", "As a writer as soon as it boots", "By copying only its DNS record"], "Its history may diverge from the current writer."),
    ("What is a safe response when a rewind cannot verify shared history?", ["Provision a fresh replica from a known-good base", "Force the rewind and ignore errors", "Accept both databases as writers"], "Unsupported histories require a clean resynchronization path."),
    ("What should an exercise stop condition trigger?", ["Halt the fault, inspect residual effects, and validate recovery", "Assume all side effects reversed", "Delete the incident record"], "Stopping injection does not automatically restore every changed resource."),
    ("When is the recovery drill fully closed?", ["After evidence, findings, and the next standby protection are verified", "At the first green application probe", "When the old region responds to ping"], "Readiness for the next failure is part of completion."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on timed failover, write gaps, client drains, and failback.",
            sort_order=22500, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the next recovery action from evidence of user impact, writer authority, replica position, and client behavior. The goal is a functioning service with one accepted data history and a tested path through the next failure.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-data-continuity-decisions", "quizzes/devops-object-storage-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not confuse traffic movement with write fencing.</li><li>Do not infer a safe failback from a restarted old database.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Recovery execution check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/backup-and-recovery": ["devops/recovery-time-budget-ledger", "devops/recovery-drill-evidence-reset"],
    "devops/multi-region-failover": ["devops/standby-admission-checklist", "devops/disaster-declaration-stop-conditions", "devops/failback-timeline-reconciliation"],
    "devops/failover-write-fencing": ["devops/failover-ordering-control-points", "devops/cutover-connection-drain-contract"],
    "devops/replica-lag-read-contract": ["devops/recovery-write-gap-ledger"],
    "devops/dns-cutover-safety": ["devops/cutover-connection-drain-contract"],
    "devops/pitr-timeline-acceptance": ["devops/failback-timeline-reconciliation"],
    "devops/incident-response": ["devops/disaster-declaration-stop-conditions", "devops/recovery-time-budget-ledger"],
    "devops/data-continuity-recovery-project": [project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Recovery execution follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))

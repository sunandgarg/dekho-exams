"""Add stateful operations and incident-quality lessons to the DevOps preview."""

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


def lesson(slug, title, summary, definition, practice, language, sample, cost, mistakes, related):
    path = "devops/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      practice=practice, language=language, sample=sample,
                      cost=cost, mistakes=mistakes, related=related))


lesson(
    "statefulset-rollout-safety", "StatefulSet rollout safety: preserve identity and data while updating",
    "Stage an ordinal rollout and verify the data format before advancing every replica.",
    "A StatefulSet manages Pods with stable ordinal identities and, when configured, persistent volume claims tied to those identities. Its rolling update normally proceeds one Pod at a time, waiting for readiness before continuing. A partition can hold lower ordinals at the previous template revision. That control does not make an incompatible on-disk format reversible or guarantee that application replicas can safely run mixed versions.",
    "A three-replica invoice index stores its shard data on separate PVCs. Back up and test the data format first, then set a rollout partition so only the highest ordinal receives the new image. Exercise reads and writes while old and new replicas coexist. The YAML fragment belongs in the StatefulSet spec and assumes three replicas; it is not a complete manifest. Check leader election, replication lag, and quorum rules before lowering the partition. If the new binary migrates disk state on startup, an image rollback might fail against that changed data. Keep a compatible reader version or restore plan. Inspect PVC retention policy before scaling down or deleting the set; a deletion setting can remove claims independently of whether the application is healthy.",
    "yaml", "spec:\n  replicas: 3\n  updateStrategy:\n    type: RollingUpdate\n    rollingUpdate:\n      partition: 2\n  persistentVolumeClaimRetentionPolicy:\n    whenDeleted: Retain\n    whenScaled: Retain",
    "The staged replica consumes the same storage and roughly the same compute as before, but the team pays in longer rollout time and mixed-version testing. Readiness only reports the configured probe; it does not confirm shard correctness or replication safety. Measure lag and user errors while the partition is held. A retained PVC keeps data after a Pod disappears, which helps recovery but continues to incur storage cost and requires an owner for cleanup.",
    ["Do not assume a Pod rollback reverses an on-disk migration.", "Do not lower the partition before mixed-version behavior is checked.", "Do not change PVC retention without tracing deletion consequences."],
    ["devops/persistent-storage", "devops/volume-snapshot-recovery", "devops/kubernetes-probes", "devops/backup-and-recovery"],
)

lesson(
    "namespace-resource-quotas", "Namespace quotas: reserve room for a safe rollout",
    "Bound a team's aggregate resource use without blocking replacement Pods during maintenance.",
    "A ResourceQuota caps aggregate consumption or object counts in a Kubernetes namespace. A LimitRange constrains or supplies per-object requests and limits. They act during admission; adding either policy does not resize Pods that already run. A namespace can be under its steady-state quota and still fail a rolling update when surge Pods need temporary headroom.",
    "A claims namespace normally requests seven CPU cores and sixteen gibibytes of memory. Set an aggregate request budget with room for one replacement Pod, then rehearse the maximum-surge rollout under the quota. The YAML block is a namespace quota, not a sizing recommendation for another cluster. Inventory existing Deployments, Jobs, and PVCs before applying it. Test a new Pod that should be admitted and one that should be denied; read the admission message rather than blaming the scheduler. If a LimitRange injects default requests, check the resulting Pod spec and quota usage. A quota can protect neighbors from runaway work but can also stop incident recovery if the only spare capacity lies beyond the namespace cap.",
    "yaml", "apiVersion: v1\nkind: ResourceQuota\nmetadata: {name: claims-budget, namespace: claims}\nspec:\n  hard:\n    requests.cpu: '9'\n    requests.memory: 22Gi\n    limits.memory: 34Gi\n    pods: '47'",
    "The quota itself costs little at runtime, yet it creates operational review when teams add workloads. Overly generous limits do not reserve node capacity; overly tight ones can prevent a replacement from being admitted. Compare quota headroom with scheduler capacity and the Deployment's surge policy. Monitor hard and used values, especially during backfills and failed Jobs. Apply per-container defaults deliberately because an injected memory limit can trigger out-of-memory kills in software never tested at that limit.",
    ["Do not size quota only for steady-state replicas.", "Do not assume quota creates nodes or storage capacity.", "Do not add a LimitRange without checking injected defaults on real Pods."],
    ["devops/kubernetes-resource-budgets", "devops/kubernetes-deployments", "devops/pod-disruption-budgets", "devops/cost-capacity-ownership"],
)

lesson(
    "database-backfill-checkpoints", "Database backfills: checkpoint progress without racing live writes",
    "Migrate existing rows in bounded batches while old and new application versions overlap.",
    "A database backfill computes or copies data for existing records after a schema change. It differs from a schema migration that merely adds a column: a large table scan can hold locks, amplify replication lag, and contend with user writes. A restartable backfill needs a stable ordering key, durable progress, and an idempotent update rule so retrying a batch does not corrupt data.",
    "A parcel service adds a normalized destination code. Deploy a reader that accepts both old and new representation, then dual-write new parcels. The worker below selects a bounded ID range and updates only rows still missing the normalized value; its application transaction must persist the last completed ID after the batch commits. The SQL fragment illustrates one batch, not the checkpoint table or driver loop. Avoid a long transaction spanning the whole table. Pace batches against user latency and replication delay, and stop if either crosses its limit. Validate counts and a sample of edge-case addresses before making the new column mandatory. Keep the old reader until rollback and retained-message windows close. If live writes can change the source field during backfill, use a version guard or recheck pass rather than trusting the first scan.",
    "sql", "UPDATE parcel_destination\nSET normalized_code = UPPER(TRIM(raw_code))\nWHERE parcel_id > 47000\n  AND parcel_id <= 47400\n  AND normalized_code IS NULL;",
    "Batch size trades fewer transactions for longer locks and larger replication bursts. A range of four hundred IDs may update far fewer than four hundred rows; measure actual writes and elapsed time. Checkpoints add state but make interruptions recoverable. A backfill can be logically correct and still harm availability through I/O pressure, so throttle on service metrics rather than a fixed sleep alone. The SQL expression is illustrative; real normalization needs validated business rules and collation behavior.",
    ["Do not hold one transaction open for the entire table.", "Do not advance the checkpoint before its batch commits.", "Do not make the new field required before old rows and clients are handled."],
    ["devops/database-change-safety", "devops/api-compatibility-window", "devops/capacity-load-testing", "devops/backup-and-recovery"],
)

lesson(
    "dead-letter-replay", "Dead-letter replay: recover failed messages without repeating their effects",
    "Separate poison messages from transient failures and replay through the normal idempotent consumer.",
    "A dead-letter destination receives messages a queue could not process under its configured failure policy. It is a holding area for investigation, not proof that the event was harmless or will be retried automatically. Replaying a message can duplicate a completed side effect when the consumer committed work but failed before acknowledgement.",
    "A royalty worker rejects a malformed payout event after a bounded attempt count. Record its event ID, failure class, original enqueue time, and the consumer revision that failed; do not put personal data into an unrestricted dead-letter log. The policy sketch is not a broker declaration. Fix the parser or data contract, then select a small replay cohort by event ID and send it through the normal consumer with the original business idempotency key. Verify ledger effects and acknowledgement count before expanding the cohort. A permanently invalid event should move to a documented manual disposition, not spin in a retry loop. Keep a separate alarm for dead-letter growth and oldest age. The broker may provide different delivery guarantees for dead-letter transfer, so test failure of the transfer path itself.",
    "text", "Royalty replay gate\nOriginal event ID: preserved\nFailure class: transient, contract, or permanent\nAttempt cap: 3 consumer deliveries\nReplay cohort: named IDs, operator, start time\nEffect guard: unique payout operation key\nStop gate: duplicate ledger write or rising failure age",
    "Dead-letter storage and investigation add cost, but infinite retries can saturate the main queue and hide useful work. Replay throughput should be limited to protect the recovered dependency. Message age matters: the business action may no longer be valid even when the parser now accepts it. Observe the original effect boundary, not only broker acknowledgements. Retain enough metadata to audit a replay while applying the same data-retention controls as the source queue.",
    ["Do not replay every failed event at once after a fix.", "Do not assign a new idempotency key to the same logical payout.", "Do not equate an empty dead-letter queue with no lost work."],
    ["devops/queue-consumer-reliability", "devops/retry-timeout-budgets", "devops/alert-design", "devops/api-compatibility-window"],
)

lesson(
    "secret-rotation-rollout", "Secret rotation rollout: update the issuer, consumer, and active connections",
    "Prove that new processes use the replacement credential before disabling the old one.",
    "Secret rotation changes a credential at its issuer and in the system that consumes it. A new value in a secret store does not guarantee that running processes reload it. Environment variables are fixed for a running container, and connection pools may keep old sessions alive even after a new credential is available. The rotation plan needs an overlap window or staged identities when the target service supports them.",
    "A claims API authenticates to a document database. Create a second narrowly scoped database identity, publish its credential through the approved secret path, and roll a small group of API Pods so they establish new connections. Observe authentication failures and connection age. The checklist is an operational contract, not a command that exposes values. When every active instance uses the new identity and a synthetic claim succeeds, disable the old identity and verify a denied login with it. If the storage system supports only one password, schedule a short controlled transition and make application refresh behavior explicit. Keep secret values out of logs, build artifacts, and support tickets. Test a failed rotation in a disposable environment so the recovery order is known.",
    "text", "Document database rotation gate\nCreate: new least-privilege identity\nDistribute: approved secret path; no build artifact\nAdopt: roll or refresh claims API instances\nVerify: new connections and claim transaction succeed\nRevoke: disable old identity at database\nNegative test: old credential denied",
    "Two valid identities add a temporary access surface, but permit a safer handoff when old and new processes coexist. A short overlap reduces exposure while increasing the risk of breaking a slow-to-refresh consumer; inventory all consumers first. Each rotation also exercises secret-manager availability and database authentication capacity. Monitor denied logins after revocation to find forgotten clients. Do not assume a mounted file refresh causes the application library to reopen its connection pool.",
    ["Do not update only the secret store while leaving the issuer unchanged.", "Do not revoke before every consumer has adopted the new identity.", "Do not retain the old credential indefinitely after cutover."],
    ["devops/secrets-and-configuration", "devops/credential-incident-rotation", "devops/graceful-pod-shutdown", "devops/service-account-token-boundaries"],
)

lesson(
    "slo-burn-rate-alerts", "SLO burn-rate alerts: page on budget consumption, not isolated spikes",
    "Use a fast and a sustained window to separate urgent impact from brief noise.",
    "An error-budget burn rate is the speed at which a service spends the failures allowed by its service-level objective. A high burn rate sustained over a short interval can justify a page; a smaller rate sustained for hours may need a different response. The alert should describe user-visible failures and include enough traffic to make a ratio meaningful.",
    "A claims API targets 99.9 percent successful requests over thirty days. Compute a failure ratio from counters, compare it with the allowed error fraction, and require both a short and a long window before paging. The PromQL fragment shows the five-minute ratio only; a complete alert also checks a longer window, excludes health checks from the user denominator, and handles low traffic. A 2 percent error ratio is twenty times the allowed 0.1 percent failure fraction. Review how much budget that burns over the chosen windows before selecting thresholds. Route the page to the owning team with a runbook that shows affected operations, current deployment revision, and a safe stop action. Test the alert with a controlled synthetic failure and confirm the notification reaches an operator.",
    "promql", "sum(rate(claim_requests_total{result=\"error\"}[5m]))\n/ clamp_min(sum(rate(claim_requests_total[5m])), 0.001)",
    "Long windows lower noise but delay detection; short windows detect quickly and can page on brief bursts. Multiple windows use more rule evaluation and require care around sparse traffic. A ratio without a minimum request count can behave oddly when almost no requests occur. Track alert firing alongside consumed error budget and operator action. A page that reliably fires but offers no useful response should be revised, not celebrated as coverage.",
    ["Do not page on every single failed request.", "Do not divide by a sparse traffic rate without a low-volume policy.", "Do not call a ratio alone a complete multiwindow alert."],
    ["devops/service-level-objectives", "devops/alert-design", "devops/observability-signals", "devops/incident-response"],
)

lesson(
    "canary-cohort-analysis", "Canary analysis: compare a small cohort without hiding its failures",
    "Use matched traffic and explicit stop criteria before widening exposure.",
    "A canary release sends a limited share of traffic to a new revision while the older revision still serves most users. Its safety depends on comparing meaningful outcomes across those revisions. A tiny cohort may not include the operation that changed; a large cohort may expose too many users before a fault is detected.",
    "A parcel pricing release starts with internal users and then five percent of eligible requests. Pin the same request types and regions in both old and new samples, or record where they differ. The policy record defines what the release controller and operator should measure; it is not a controller API. Compare error rate, p95 latency, and a business check such as duplicate prices. Wait long enough for delayed queue effects to appear before promotion. If the stop threshold is crossed, return new traffic to the old revision while checking whether side effects or schema changes need separate recovery. A feature flag can stop a code path, but it is not a substitute for measuring the actual served revision. Record cohort size and confidence limits so a clean result from seventeen requests is not called strong evidence.",
    "text", "Parcel pricing canary\nExposure: internal cohort, then 5 percent of eligible traffic\nCompare: same route, region, and request mix\nStop: error ratio above 1.8 percent or p95 above 740 ms\nCheck: duplicate price events and delayed queue effects\nPromote: named decision after observation window\nRecover: route old revision and inspect completed writes",
    "Running two revisions consumes extra compute and monitoring effort. A longer observation window improves evidence but slows delivery; a shorter one can miss rare or delayed defects. Metrics tagged by revision increase cardinality, so limit tags to stable identifiers. Evaluate both absolute user impact and relative comparison: a canary can look better than an already failing baseline while still violating the service objective. Preserve the decision record with the release digest.",
    ["Do not promote on a small, unrepresentative sample.", "Do not compare different routes or regions without noting the bias.", "Do not call traffic rollback a reversal of completed writes."],
    ["devops/progressive-delivery", "devops/feature-flag-release", "devops/release-evidence-record", "devops/service-level-objectives"],
)

lesson(
    "incident-review-actions", "Incident reviews: turn a timeline into tested corrective work",
    "Preserve evidence, separate contributing conditions, and assign verifiable follow-ups.",
    "An incident review reconstructs what happened, how users were affected, which controls behaved as expected, and which conditions increased impact or recovery time. It should explain decisions with the information available at each moment. A timeline alone is insufficient if nobody owns the changes needed to reduce recurrence or detection delay.",
    "A claims outage followed a route edit and a stalled database failover. Record the first failed user transaction, detection time, page delivery, operator acknowledgement, mitigation, and recovery verification. The text block is an action template, not an incident narrative. Separate the route trigger from conditions that prolonged the event, such as a stale runbook or missing synthetic probe. Attach evidence only through approved incident storage, without copying private customer payloads into a broad document. Give every corrective action an owner, due date, and acceptance test. For example, a route test should fail on the bad configuration before deployment; a failover drill should include the read-write user path. Revisit completed actions after the next exercise to check whether they actually shorten recovery. Avoid using the review to infer individual blame from incomplete logs.",
    "text", "Claims incident action\nCondition: route accepted but backend path failed\nOwner: edge platform team\nChange: pre-promotion external synthetic request\nAcceptance: bad route blocks promotion in test\nDeadline: next controlled release window\nVerification: exercise result attached to incident record",
    "Review time competes with delivery work, but a short list of tested changes is more useful than dozens of vague recommendations. Store only necessary logs and decisions under retention rules. A corrective item that merely says improve monitoring has no observable completion condition. Track action age and repeat incidents, not the number of documents published. Some failures remain possible after a fix; state the residual risk and the decision owner.",
    ["Do not stop at a chronology without assigned changes.", "Do not call an action complete because a ticket closed without its acceptance test.", "Do not publish private customer evidence in a broad review."],
    ["devops/incident-response", "devops/log-pipeline-retention", "devops/slo-burn-rate-alerts", "devops/resilience-game-day-project"],
)

lesson(
    "ephemeral-environment-controls", "Ephemeral environments: keep preview access and cost bounded",
    "Build isolated review environments without copying production credentials or data.",
    "An ephemeral environment is a temporary deployment tied to a change or review period. It can expose integration faults before promotion, but it is still an environment with network access, data, and cost. A preview should have a known owner, expiration, access boundary, synthetic test data, and cleanup verification.",
    "A billing API pull request needs a temporary namespace to exercise a new route and migration. Build the exact image digest under test and provision a namespace with a unique change identifier. Use a synthetic ledger dataset and a test-only database identity. The manifest is a namespace marker, not a complete isolation policy: add quota, network policy, RBAC, and a scoped deploy identity before untrusted code runs. Never expose production Secrets to pull-request workflows. Record the deployment URL only in the approved review surface, limit ingress to reviewers, and destroy the environment after merge or timeout. Check that PVCs, snapshots, load balancers, and DNS entries were removed; deleting a namespace may not remove every external resource. Measure cost by review ID so lingering previews are visible.",
    "yaml", "apiVersion: v1\nkind: Namespace\nmetadata:\n  name: billing-review-47\n  labels:\n    app.kubernetes.io/part-of: billing-api\n    ai-trove-owner: billing-platform\n    ai-trove-purpose: pull-request-review",
    "Preview environments spend compute, database, edge, and log capacity while they exist. Shared dependencies lower cost but can make tests interfere with each other, so decide what must be isolated. A broad public preview URL can expose unfinished features or synthetic-but-sensitive metadata. Use an expiration controller or scheduled cleanup with an audit trail. A cleanup job that reports success while leaving cloud load balancers behind has not met the cost boundary.",
    ["Do not give untrusted pull-request code production credentials.", "Do not assume namespace deletion cleans up every external asset.", "Do not present a preview as a production-equivalent test without naming shared dependencies."],
    ["devops/github-actions-security", "devops/namespace-resource-quotas", "devops/network-policy-isolation", "devops/cost-capacity-ownership"],
)

lesson(
    "dependency-patch-campaign", "Dependency patch campaigns: update, test, and prove the running image",
    "Treat a security advisory as an inventory and rollout problem, not a version edit alone.",
    "A dependency patch campaign identifies affected artifacts, replaces the vulnerable component, verifies behavior, and confirms that old artifacts are no longer running. A lockfile update changes future builds; it does not patch already deployed images or retained worker processes. The required urgency depends on exploitability, exposure, and service impact.",
    "A document renderer uses a library with a disclosed parsing flaw. Query the build inventory for images containing the affected package, identify which are reachable by untrusted PDFs, and prioritize those services. Update the lockfile and base image as needed, build once, run malformed-file regression tests, and record the new digest. The shell block shows package verification and test commands, not the inventory query or deployment gate. Roll out the digest through a canary and read back each running Pod's image ID. If the flaw can be reached from a queue, include workers that are not behind the public API. Keep the old digest in a quarantine list; do not delete it before rollback planning is complete, but do not allow accidental redeployment. Verify that the runtime package version changed, not only the manifest text.",
    "bash", "npm ci\nnpm ls pdf-parser --all\nnpm run test:malformed-documents\nnpm run build",
    "A rushed patch can break parsing or increase CPU cost. A staged rollout uses extra capacity and time but provides evidence of impact. Inventory errors are common when transitive dependencies, base images, or background workers are omitted. Scanners can disagree on package metadata, so inspect the built artifact and actual runtime when the decision matters. Keep a record of affected services, deployed digests, and exceptions with an expiry; a ticket closed at merge time does not prove risk has left production.",
    ["Do not confuse a lockfile change with a deployed fix.", "Do not ignore background workers that process the same untrusted input.", "Do not close the campaign before checking running image IDs."],
    ["devops/ci-cache-boundaries", "devops/supply-chain-verification", "devops/artifact-promotion", "devops/canary-cohort-analysis"],
)


titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/stateful-recovery-project"
quiz_path = "quizzes/devops-stateful-operations"
titles[project_path] = "Project: stage and recover a stateful release"
titles[quiz_path] = "DevOps stateful operations decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


groups = [
    ("Stateful change and replay", "Stage persistent workloads and make delayed work recoverable.", ["statefulset-rollout-safety", "database-backfill-checkpoints", "dead-letter-replay", "secret-rotation-rollout"]),
    ("Capacity and release signals", "Bound namespace demand and use user-facing evidence to advance a release.", ["namespace-resource-quotas", "slo-burn-rate-alerts", "canary-cohort-analysis"]),
    ("Follow-through and review environments", "Close incident actions and temporary deployment access with evidence.", ["incident-review-actions", "ephemeral-environment-controls", "dependency-patch-campaign"]),
]
hub = by_path[course]
for title, summary, slugs in groups:
    paths = ["devops/" + slug for slug in slugs]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": paths})
    hub["body"] += f"<h2>{html.escape(title)}</h2><p>{html.escape(summary)}</p>" + links(paths)
hub["updated_at"] = stamp

for order, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "operations"],
               sort_order=18200 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
                   f"<p>{html.escape(item['practice'])}</p>"
                   f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
                   f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
                   + "<h3>Common Mistakes</h3><ul>"
                   + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
                   + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]]))
    rows.append(row)

project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Exercise a partitioned rollout, bounded backfill, failed-message replay, and recovery decision.",
               difficulty="Advanced", sort_order=18290,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in ["devops/statefulset-rollout-safety", "devops/database-backfill-checkpoints", "devops/dead-letter-replay", "devops/volume-snapshot-recovery"]]}
project["body"] = (
    "<p>This project rehearses an upgrade to a stateful invoice index without treating Pod readiness as proof of data safety. Use a disposable cluster, a synthetic ledger, and a storage driver that supports snapshots. Record the old image digest, schema version, message position, and recovery objective before changing anything.</p>"
    "<h2>Stage the change</h2><p>Create three StatefulSet replicas with retained claims and a tested backup. Hold the rollout partition at the highest ordinal, update only that replica, and run mixed-version reads. Add an optional normalized code field to a synthetic table, dual-write new rows, and backfill old rows in bounded ID ranges with a durable checkpoint. Introduce one malformed queue event and move it to the dead-letter destination after the configured attempt cap. Alert on oldest failed-event age.</p>"
    "<pre><code class=\"language-text\">Invoice release evidence\nStatefulSet: partition held, ordinal and PVC recorded\nBackfill: committed checkpoint and row-count sample\nQueue: original event ID and unique effect key\nSnapshot: restored into a separate claim\nStop gate: replication lag, user error, or duplicate effect\nDecision: named operator with observed digest and schema</code></pre>"
    "<h2>Fail and recover</h2><p>Interrupt the backfill after one committed batch and restart it. Confirm that the checkpoint resumes without duplicate updates. Fix the malformed event, replay only its original ID through the normal consumer, and verify one ledger effect. Restore the snapshot to a new PVC and run a compatible database query; do not overwrite the only working volume. Advance the StatefulSet partition only when old and new replicas remain healthy under the same traffic mix. If the new version changes its on-disk format, exercise the actual restore path rather than claiming an image rollback is enough.</p>"
    "<h2>Cost and verification</h2><p>The test uses extra storage, temporary compute, queue retention, and operator review time. Capture actual batch duration, replication lag, restored transaction position, and replay outcome. A green controller status is not proof of correct invoices. Clean up disposable claims only after the recovery evidence has been retained under the agreed policy.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not advance a partition because a single Pod is merely Ready.</li><li>Do not advance the backfill checkpoint before its transaction commits.</li><li>Do not replay with a fresh business key.</li></ul>"
    "<h2>Connected lessons</h2>" + links(["devops/statefulset-rollout-safety", "devops/database-backfill-checkpoints", "devops/dead-letter-replay", "devops/volume-snapshot-recovery", "devops/secret-rotation-rollout", project_hub]))
rows.append(project)
project_index = by_path[project_hub]
project_index["data"]["modules"][0]["lessons"].append(project_path)
project_index["body"] += "<h2>Stateful recovery exercise</h2>" + links([project_path])
project_index["updated_at"] = stamp

questions = [
    ("What does a StatefulSet partition hold back?", ["Template updates for lower ordinals", "All PVC writes", "Every client request"], 0, "A partition stages which ordinal Pods receive the new template."),
    ("Why reserve quota above steady-state requests?", ["Replacement or surge Pods need temporary admission room", "Quota provisions new nodes", "Quota repairs a failing image"], 0, "A rollout can need more resources than steady state."),
    ("When should a backfill checkpoint advance?", ["After its batch commits", "Before the first UPDATE", "When the worker starts"], 0, "Progress must describe durable completed work."),
    ("What identity should a replayed payout retain?", ["The original logical operation key", "A fresh business key", "Only a new broker delivery tag"], 0, "The effect boundary must recognize a repeated attempt."),
    ("What completes credential rotation?", ["New consumers work and the old credential is denied", "A new secret value exists", "The old connection pool stays open"], 0, "Issuer and active consumers both matter."),
    ("What does a high SLO burn rate measure?", ["Fast consumption of the allowed failure budget", "High CPU alone", "The number of open tickets"], 0, "It ties user-visible failures to the objective."),
    ("What weakens a canary comparison?", ["Different request mixes between old and new revisions", "A recorded image digest", "A clear stop threshold"], 0, "Cohort differences can dominate revision differences."),
    ("What makes an incident action verifiable?", ["An owner and acceptance test", "A vague request to improve monitoring", "A closed document"], 0, "The change needs an observable completion condition."),
    ("What must a preview environment exclude?", ["Production credentials and customer data", "Synthetic test transactions", "An expiry owner"], 0, "Temporary code can still access real systems if given real secrets."),
    ("What proves a dependency patch reached production?", ["The running image contains the new package revision", "A lockfile merge alone", "A scanner ticket marked closed"], 0, "Existing images remain unchanged until replaced."),
    ("Why test a restored snapshot?", ["Capture success does not prove application-consistent recovery", "A snapshot deletes the source volume", "A restore always changes the schema"], 0, "Recovery must be checked at the application level."),
    ("What should follow dead-letter replay?", ["Verify the business effect and acknowledgement", "Only count published replay messages", "Ignore oldest failure age"], 0, "Broker movement alone does not establish correct outcomes."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve checks on stateful rollout, replay, rotation, alerting, and patch proof.",
            sort_order=18300, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in ["devops/statefulset-rollout-safety", "devops/database-backfill-checkpoints", "devops/dead-letter-replay", "devops/slo-burn-rate-alerts", "devops/dependency-patch-campaign"]],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(answer - index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, answer, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the operational result supported by the evidence. Each answer points to a concrete failure or verification boundary.</p><h2>Review these lessons</h2>" + links([item["path"] for item in quiz["data"]["related"]]) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-delivery", "quizzes/devops-operations", "quizzes/devops-platform-reliability", "quizzes/devops-advanced-delivery", "quizzes/devops-resilience-and-response", "quizzes/devops-ownership-and-recovery"]) + "<h3>Common Mistakes</h3><ul><li>Do not mistake controller status for a business transaction result.</li><li>Do not mistake a merged patch for a running patch.</li></ul>"
rows.append(quiz)
quiz_index = by_path[quiz_hub]
quiz_index["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_index["body"] += "<h2>Stateful operations check</h2>" + links([quiz_path])
quiz_index["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": target, "title": titles[target]} for target in [project_path, quiz_path])

for source, targets in {
    "devops/persistent-storage": ["devops/statefulset-rollout-safety"],
    "devops/kubernetes-resource-budgets": ["devops/namespace-resource-quotas"],
    "devops/database-change-safety": ["devops/database-backfill-checkpoints"],
    "devops/queue-consumer-reliability": ["devops/dead-letter-replay"],
    "devops/secrets-and-configuration": ["devops/secret-rotation-rollout"],
    "devops/service-level-objectives": ["devops/slo-burn-rate-alerts"],
    "devops/progressive-delivery": ["devops/canary-cohort-analysis"],
    "devops/incident-response": ["devops/incident-review-actions"],
    "devops/github-actions-security": ["devops/ephemeral-environment-controls"],
    "devops/supply-chain-verification": ["devops/dependency-patch-campaign"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1,
                  "new_quiz_banks": 1, "total_records": len(rows)}))

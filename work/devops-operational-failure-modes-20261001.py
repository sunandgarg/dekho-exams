"""Add advanced DevOps lessons on failure and control-plane boundaries."""

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
    "replica-lag-read-contract", "Replica lag: define when a read is allowed to be stale",
    "Keep acknowledged writes visible where the user expects them and make failover loss measurable.",
    "An asynchronous database replica applies committed changes after the primary accepts them. The delay between those events is replication lag. A query routed to the replica can therefore return an older value even though the write succeeded. Lag is a read-consistency issue during normal operation and a possible data-loss window when a lagging replica is promoted after primary failure.",
    "A claims API writes a settlement state and immediately displays it to the operator. Route the confirmation read to the primary or require a read position at least as recent as the write; a generic read pool can show the previous state. The SQL fragment reads replication position on a PostgreSQL primary and replay position on a standby, so run each statement against its named role rather than as one transaction. Monitor both byte distance and elapsed replay age, then inject delayed replication in a disposable system and observe the user path. Before promoting a standby, record the last confirmed write and the replay position on the candidate. After promotion, reconcile external acknowledgements with the new primary; an asynchronous replica may lack acknowledged transactions. State a recovery-point objective in terms of business records, not only seconds of lag. A healthy connection to the standby does not establish that it has caught up.",
    "sql", "-- Run on the primary\nSELECT pg_current_wal_lsn() AS primary_lsn;\n-- Run separately on the standby\nSELECT pg_last_wal_replay_lsn() AS standby_replay_lsn;",
    "Reading from replicas can reduce primary query pressure but adds lag measurement, routing rules, and failover reconciliation. Stronger synchronous durability can increase commit latency or block writes when a required standby is unavailable; the exact trade depends on configuration. Position alone does not prove a business effect was applied correctly, so retain an end-to-end confirmation check. Alert on sustained lag relative to the service's tolerance and on a stalled replay process.",
    ["Do not route immediate read-after-write confirmation to an unconstrained replica.", "Do not equate a reachable standby with a caught-up standby.", "Do not promote without recording the potential acknowledged-write gap."],
    ["devops/database-pool-pressure", "devops/multi-region-failover", "devops/backup-and-recovery", "devops/synthetic-transaction-monitoring"],
)

lesson(
    "partition-rebalance-safety", "Consumer rebalances: preserve ordering and effect ownership",
    "Commit progress only after the external effect is durable and recover partition handoffs.",
    "A partitioned event log orders records within each partition, not across an entire topic. Consumers in a group divide partition ownership; a membership change can reassign a partition. A consumer that commits its offset before its business effect is durable can skip work after a crash. A consumer that performs the effect and crashes before committing may process that record again after rebalance.",
    "A payout stream uses account ID as the partition key so updates for one account retain partition order. Process each record under its original operation key, commit the ledger effect, then commit the corresponding offset. The text block is a handoff contract, not broker configuration. During a rolling update, stop fetching new records, finish or abandon in-flight work within the shutdown deadline, and let the next owner retry uncommitted records. Verify duplicate delivery by killing a worker after the ledger commit but before offset commit. Adding partitions may change the hash-to-partition mapping for future records, so test account ordering across the expansion boundary before assuming a stable key gives the same partition forever. Record consumer lag by partition and the oldest unprocessed event age; an aggregate lag can hide one hot account.",
    "text", "Payout partition handoff\nKey: account ID\nEffect key: original payout operation ID\nOn record: validate, persist ledger effect, then commit offset\nOn revoke: stop fetch; finish bounded in-flight work\nOn restart: retry uncommitted record under same effect key\nCheck: one ledger effect after forced rebalance",
    "More partitions can increase parallelism but also metadata, open fetches, and rebalance work. A single hot key remains serialized on one partition even when worker count rises. Committing offsets in every record can add broker traffic; batching commits reduces overhead but increases the retry window. Idempotency at the ledger boundary is therefore necessary even with careful offset order. Test a rebalance under load, not only a clean shutdown.",
    ["Do not claim global event order across partitions.", "Do not commit an offset before the business effect is durable.", "Do not change partition count without checking key ordering assumptions."],
    ["devops/queue-consumer-reliability", "devops/dead-letter-replay", "devops/event-schema-evolution", "devops/graceful-pod-shutdown"],
)

lesson(
    "metric-cardinality-budget", "Metric cardinality: keep observability usable during a surge",
    "Limit label combinations before one request ID creates one time series per request.",
    "A metric time series is identified by its name and complete label set. Every distinct combination creates another series. Labels with unbounded values, such as request IDs or customer email addresses, can grow storage, memory, and query work with traffic volume. Histograms multiply that effect across bucket, sum, and count series, so a label that looks small on one counter can be expensive when copied everywhere.",
    "A claims gateway emits a request counter. Keep stable route templates, outcome class, and service revision as metric labels; place individual request IDs in trace or log records under the appropriate retention policy. The PromQL expression groups current request series by route so an operator can spot a route explosion. It is an inspection query, not a cardinality limit. Review the number of active series before and after each instrumentation change and set a collection budget per service. If a route label contains raw account numbers, replace it with the registered route template at the instrumentation point; dropping it later in the pipeline may already have burdened the agent. Run a load test with many distinct account IDs and verify series growth stays bounded while the error-rate alert still separates useful route classes.",
    "promql", "count by (route) (claims_requests_total)",
    "Fewer labels reduce ingestion and query cost but remove dimensions from aggregate metrics. Use traces for individual requests and logs for carefully controlled detail. A query that scans every series can itself be costly, so measure head-series count and ingestion rate with the monitoring system's own metrics rather than repeatedly issuing broad exploratory queries during an incident. Keep the remaining labels stable enough for dashboards and alert rules to survive releases.",
    ["Do not label a counter with request ID, email, or raw path parameters.", "Do not assume a cheap counter label stays cheap on a histogram.", "Do not remove every dimension and leave operators unable to locate a failing route."],
    ["devops/observability-signals", "devops/alert-design", "devops/trace-context-propagation", "devops/log-pipeline-retention"],
)

lesson(
    "trace-sampling-decisions", "Trace sampling: retain useful failures without flooding storage",
    "Choose the decision point according to the evidence needed and monitor dropped spans.",
    "Trace sampling decides which distributed requests are retained for analysis. Head sampling chooses near the start of a trace, which is cheap but cannot know whether a later span fails. Tail sampling waits to inspect much of the trace, enabling error or latency criteria at the cost of buffering, state, and a later decision. Neither method repairs missing propagation between services.",
    "A parcel checkout has high traffic but rare payment timeouts. Keep a low, consistent baseline of successful traces and a higher share of error and slow traces. The text policy is a design record; implement it in the chosen collector and SDK with supported settings. Send all spans of a trace to the same decision point, otherwise a tail sampler may see only a fragment. Size the wait period to cover the expected trace duration and set a memory limit for bursts. During a controlled timeout, verify the collector retains the trace containing the downstream error and that trace IDs connect to logs. Measure refused or dropped spans at both SDK and collector. If a head sampler already discarded the trace, a later tail rule cannot recover it. Keep secrets and personal data out of attributes regardless of sampling rate.",
    "text", "Parcel trace policy\nBaseline: consistent low-rate successful traces\nPriority: errors and slow checkout paths\nTail wait: covers measured request duration\nRouting: all spans of one trace reach one decision point\nGuard: bounded collector memory and drop alert\nProof: injected payment timeout appears with correlated logs",
    "Head sampling uses less collector memory and exports less data early; tail sampling provides richer selection but must buffer spans while a decision is pending. More retained traces increase storage and transfer cost. A policy optimized only for errors can miss slow successful requests or a broken sampler. Track accepted, sampled, and dropped spans, and compare with independently measured request failures. Treat sampling as a data-volume control, not a substitute for error-rate metrics.",
    ["Do not expect tail sampling to recover traces dropped at the head.", "Do not split one trace across independent tail samplers without consistent routing.", "Do not put private payloads into spans because most traces are sampled out."],
    ["devops/trace-context-propagation", "devops/metric-cardinality-budget", "devops/log-pipeline-retention", "devops/incident-response"],
)

lesson(
    "stuck-finalizer-recovery", "Stuck finalizers: finish cleanup before removing the guard",
    "Diagnose a terminating resource without orphaning external storage or network assets.",
    "A Kubernetes finalizer keeps an object present after deletion is requested so a controller can perform cleanup. The API records a deletion timestamp; the resource remains until the controller removes its finalizer. A stuck finalizer is therefore evidence of unfinished cleanup or a controller that cannot complete its work. Removing it by hand can leave cloud resources, volumes, or dependent objects behind.",
    "A preview namespace remains Terminating after its branch was merged. Read the namespace's deletion timestamp, conditions, finalizers, and remaining namespaced resources. The commands are read-only and assume the current context is the disposable cluster. Check whether the responsible controller is healthy and has permission to delete external load balancers and volumes. Restore that controller or perform the specific cleanup under a tracked incident record. Only after confirming the external objects are gone should an authorized operator consider removing a finalizer, and that procedure depends on the resource type. Verify cloud inventory after deletion; an absent namespace does not prove every billable asset was removed. Preserve any recovery snapshot before deleting claims.",
    "bash", "kubectl get namespace billing-review-47 -o yaml\nkubectl get all -n billing-review-47\nkubectl get pvc -n billing-review-47\nkubectl get events -n billing-review-47 --sort-by=.lastTimestamp",
    "Waiting for the correct controller may prolong preview cost, but bypassing cleanup can create a larger orphan bill or data-retention failure. Listing resources in a terminating namespace can miss provider-owned assets, so reconcile with external inventory. Deletion operations may be retried and must tolerate partial completion. Record which finalizer owner failed and whether the cleanup code needs a fix; merely clearing the field hides the recurring fault.",
    ["Do not strip a finalizer merely to make a namespace disappear.", "Do not assume kubectl get all lists every namespaced resource.", "Do not delete the only recovery volume before verifying the retained snapshot."],
    ["devops/ephemeral-environment-controls", "devops/persistent-storage", "devops/volume-snapshot-recovery", "devops/cost-capacity-ownership"],
)

lesson(
    "policy-exception-expiry", "Policy exceptions: make a temporary bypass expire and prove its scope",
    "Record one owner, one affected workload, one compensating control, and a removal test.",
    "A policy exception permits a narrowly defined action that the ordinary deployment or admission rule would reject. It should not turn a cluster-wide rule off for convenience. The exception needs a bounded target, business reason, expiry, owner, approval record, and evidence that the baseline rule still denies all other workloads. An expiry timestamp in a ticket is only useful if a process acts on it.",
    "A document conversion worker needs a temporary write path while its volume driver is upgraded. Keep the admission rule in force for the namespace and define a workload-specific exception using the chosen policy engine's supported mechanism. The text record is a review template, not an admission manifest. Test one allowed admission for the named worker and one denied admission for a similar Pod. Apply a compensating filesystem restriction and monitor writes during the window. At expiry, remove the exception, rerun both tests, and check the running workload no longer depends on it. If the upgrade is incomplete, renew through a fresh risk decision rather than silently changing the date. Inventory exceptions from the policy system, not only from a spreadsheet, so an abandoned rule cannot survive indefinitely.",
    "text", "Temporary admission exception\nWorkload: document-converter in render namespace\nReason: volume-driver transition\nOwner: render platform team\nExpiry: 2026-10-18 18:00 UTC\nCompensation: read-only root plus named writable mount\nProof: named Pod allowed; peer Pod denied\nRemoval: delete exception and repeat both admission tests",
    "Narrow exceptions demand review and test time but preserve the default control for other workloads. An open-ended exception saves immediate work while increasing exposure and making future audits harder. Policy-engine logs can show admissions, yet they may not reveal all runtime effects; pair admission checks with a workload behavior test. Track exception age and the count of workloads actually matching it, and page the owner before expiry when removal could break service.",
    ["Do not disable a namespace-wide or cluster-wide rule for one workload.", "Do not rely on a ticket expiry without checking the live policy object.", "Do not remove an exception without verifying the repaired workload path."],
    ["devops/admission-policy-guardrails", "devops/container-runtime-restrictions", "devops/release-evidence-record", "devops/incident-review-actions"],
)

lesson(
    "break-glass-access", "Break-glass access: recover control without permanent privilege",
    "Make emergency authority time-bounded, attributable, and revocable.",
    "Break-glass access is an emergency path to perform an operation when ordinary approval or identity systems cannot meet the incident deadline. It is a deliberately exceptional privilege, not a second everyday administrator account. The path needs a scope, independent audit record, expiration, and a way to disable it once normal control returns. A recovery design that relies on the failed identity provider for every step may not work during an identity outage.",
    "A cluster incident blocks the usual deployment identity while a faulty admission policy prevents replacement Pods. An incident commander authorizes a named operator to use an emergency role for the affected namespace. The text block specifies the evidence to retain; the exact credential issuance and access checks depend on the platform. Before use, test that the role can patch the single policy binding but cannot read unrelated customer secrets. During use, log the actor, incident, command, object diff, and result to a separately protected audit destination. Revoke the credential on recovery, compare live state with Git, and file the minimal corrective change. Drill the path periodically with a harmless resource in a disposable environment. Avoid shared static passwords whose use cannot be attributed.",
    "text", "Emergency cluster access gate\nIncident: named response record\nActor: individually identified operator\nScope: one namespace policy binding\nDuration: short automatic expiry\nAudit: independent command and object-diff record\nExit: revoke credential, reconcile desired state, review use",
    "An emergency role adds a sensitive credential and a monitoring burden, but can shorten recovery when regular control fails. Too little scope can make it useless; too much makes compromise expensive. Pre-test its exact recovery action and deny unrelated reads. Automatic expiry and post-incident reconciliation reduce persistent privilege, but they do not undo changes made while the role was active. Keep a second operator or reviewer available for high-impact changes when the incident permits it.",
    ["Do not make the only recovery path depend on the broken identity service.", "Do not share an unattributed emergency credential.", "Do not leave emergency privilege active after normal access returns."],
    ["devops/kubernetes-rbac", "devops/gitops-emergency-change", "devops/credential-incident-rotation", "devops/incident-response"],
)

lesson(
    "runbook-automation-guardrails", "Runbook automation: put a stop gate before the irreversible step",
    "Constrain targets, retries, and verification in incident scripts.",
    "A runbook automation turns a repeatable response procedure into a command or workflow. Automation removes operator typing errors but can also repeat a mistaken action across every target faster than a person would. Its safety comes from explicit preconditions, a limited target set, a dry-run or read-only preview when possible, and a postcondition that measures the user-facing result.",
    "A claims incident requires pausing a queue consumer to protect a failing database. Build a script that first reads the current cluster, namespace, Deployment UID, replica count, and queue age. Require an incident ID and a named target; reject a wildcard namespace. The shell block illustrates a read-only preflight and deliberately stops before mutation. In the complete runbook, show the expected new replica count and allow a bounded approval to scale only that Deployment. After the action, verify the targeted Pods stop fetching while existing work drains, and watch the upstream backlog. Set a maximum pause duration and a separate resume path. If a retry sees the deployment already paused, it should report that state instead of assuming its prior attempt failed. Exercise both success and partial-failure paths before using the script in production.",
    "bash", "set -euo pipefail\nincident_id=INC-47\nnamespace=claims\ndeployment=claims-queue-worker\ntest -n \"$incident_id\"\nkubectl config current-context\nkubectl get deployment \"$deployment\" -n \"$namespace\" -o jsonpath='{.metadata.uid} {.spec.replicas}'\nkubectl get pods -n \"$namespace\" -l app=claims-queue-worker",
    "Preflight checks and bounded approvals add seconds during an incident, but prevent a typo from affecting a whole cluster. Dry-run support differs by operation and may not predict external side effects, so the script also needs a measured postcondition. Repeated polling and retries can overload an already failing API server; use limited attempts and timeouts. Keep the manual recovery procedure available if automation itself or its credentials fail.",
    ["Do not make a read-only preflight appear to perform the mitigation.", "Do not accept an unbounded target selector or retry loop.", "Do not declare success until the intended user and queue effects are observed."],
    ["devops/incident-response", "devops/overload-shedding", "devops/queue-consumer-reliability", "devops/break-glass-access"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/failure-boundary-drill-project"
quiz_path = "quizzes/devops-failure-boundaries"
titles[project_path] = "Project: drill replica lag, replay, and incident control"
titles[quiz_path] = "DevOps failure-boundary decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


groups = [
    ("Data and replay failure modes", "Protect acknowledged writes and partition ownership through failure.", ["replica-lag-read-contract", "partition-rebalance-safety"]),
    ("Telemetry under pressure", "Control series and trace volume without losing failure evidence.", ["metric-cardinality-budget", "trace-sampling-decisions"]),
    ("Control-plane recovery", "Complete deletion and constrain exceptional incident authority.", ["stuck-finalizer-recovery", "policy-exception-expiry", "break-glass-access", "runbook-automation-guardrails"]),
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
               sort_order=18600 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Rehearse stale reads, consumer handoff, telemetry pressure, and bounded emergency action.",
               difficulty="Advanced", sort_order=18690,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project_related = ["devops/replica-lag-read-contract", "devops/partition-rebalance-safety", "devops/metric-cardinality-budget", "devops/trace-sampling-decisions", "devops/stuck-finalizer-recovery", "devops/runbook-automation-guardrails"]
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>This drill tests a synthetic payout service at points where a green Pod or successful HTTP response can hide lost work. Use a disposable database, event log, collector, and cluster. Record the initial primary and standby positions, consumer offsets, active time series, trace drop rate, and current access policy before injecting failure.</p>"
    "<h2>Induce bounded faults</h2><p>Delay standby replay, acknowledge a payout write, and read from the standby. Record whether the old value appears and route the confirmation read to the primary. Kill a consumer after its ledger effect commits but before its offset commits; verify a replacement retries the same record without a second ledger effect. Add many distinct synthetic account IDs to request traffic and check that metric-series count remains bounded. Generate one payment timeout and confirm the trace selection path retains its spans without sensitive data.</p>"
    "<pre><code class=\"language-text\">Failure-boundary evidence\nPrimary write ID and standby replay position\nOriginal event ID, partition, offset, one ledger effect\nSeries count before and after unique account IDs\nInjected timeout trace ID and collector drop count\nEmergency actor, target, expiry, and observed postcondition\nRecovery: user transaction succeeds after mitigation</code></pre>"
    "<h2>Recover control</h2><p>Create a disposable resource whose cleanup controller is temporarily unavailable, request deletion, and inspect its finalizer. Restore the controller and verify cleanup finishes without manually stripping the field. Rehearse a read-only incident preflight for pausing the payout consumer, then perform the mutation only through a reviewed, target-limited procedure. Restore normal operation and revoke any temporary role. Record a policy exception only if the baseline admission rule would otherwise block the recovery, and prove that the exception no longer exists at its expiry.</p>"
    "<h2>Cost and verification</h2><p>The exercise consumes extra database, broker, collector, and operator capacity. Measure replay lag, duplicate-effect count, metric-series growth, dropped spans, and deletion completion time. A successful script exit is insufficient if the wrong Deployment was changed or a customer-facing payout remains stale. Retain the incident evidence under the team policy and remove synthetic records after verification.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not confuse the committed consumer offset with a durable payout effect.</li><li>Do not remove a finalizer before completing its cleanup.</li><li>Do not call a sampled trace a complete account of all traffic.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, "devops/policy-exception-expiry", "devops/break-glass-access", project_hub]))
rows.append(project)
project_index = by_path[project_hub]
project_index["data"]["modules"][0]["lessons"].append(project_path)
project_index["body"] += "<h2>Failure-boundary drill</h2>" + links([project_path])
project_index["updated_at"] = stamp

questions = [
    ("What does asynchronous replica lag permit?", ["A successful write followed by a stale replica read", "Every standby read sees the latest commit", "A standby becomes writable without promotion"], 0, "Replay can trail a committed primary write."),
    ("What should happen before a consumer offset commit?", ["The business effect becomes durable", "The worker merely receives the record", "The partition count changes"], 0, "A committed offset must not skip unfinished effects."),
    ("Which metric label creates an unbounded series risk?", ["A unique request ID", "A fixed outcome class", "A small route template set"], 0, "Each distinct label combination is another series."),
    ("What can tail sampling inspect that head sampling cannot know early?", ["A later downstream failure in the trace", "The initial trace ID", "The service name at the root"], 0, "Tail decisions occur after more spans arrive."),
    ("Why might a deleted Kubernetes object remain visible?", ["A finalizer waits for controller cleanup", "Every deletion waits for a new image", "Its DNS TTL has not elapsed"], 0, "Deletion is marked before finalizer completion."),
    ("What makes a policy exception temporary in practice?", ["A live expiry process and removal test", "An unreviewed ticket date", "A cluster-wide rule disabled forever"], 0, "The actual policy object must be removed and checked."),
    ("What identifies emergency access use?", ["A named actor and independent audit record", "One shared static password", "A general administrator session without incident ID"], 0, "Attribution and scope are part of recovery control."),
    ("What does a runbook preflight prove?", ["The intended target and current state before mutation", "The mitigation already succeeded", "The API server cannot fail later"], 0, "A read-only preflight cannot perform the action."),
    ("What remains after a lagging standby is promoted?", ["A possible gap in acknowledged writes that needs reconciliation", "Proof that no transactions were lost", "Automatic repair of every external effect"], 0, "Promotion does not invent changes that never reached the candidate."),
    ("Why can a consumer retry an already completed effect?", ["It crashed after the effect but before offset commit", "The event schema is optional", "The metric label was bounded"], 0, "The effect and broker offset are separate durability steps."),
    ("What is a tail sampler's operational cost?", ["Buffered state and memory while waiting for spans", "No storage or routing requirement", "Elimination of all missing propagation"], 0, "Tail selection needs time and state."),
    ("When is manual finalizer removal defensible?", ["Only after its purpose and cleanup are understood and completed another way", "Whenever a namespace takes longer than one minute", "Before checking external assets"], 0, "Bypassing the guard can orphan resources."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve checks on stale reads, partition ownership, telemetry budgets, and controlled recovery.",
            sort_order=18700, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(answer - index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, answer, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the decision supported by the failure evidence. The questions separate controller status, durable effects, and user-visible recovery.</p><h2>Review these lessons</h2>" + links(project_related) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-system-boundaries", "quizzes/devops-stateful-operations", "quizzes/devops-operations"]) + "<h3>Common Mistakes</h3><ul><li>Do not infer a complete trace from one retained span.</li><li>Do not infer a durable business effect from a committed broker offset.</li></ul>"
rows.append(quiz)
quiz_index = by_path[quiz_hub]
quiz_index["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_index["body"] += "<h2>Failure-boundary check</h2>" + links([quiz_path])
quiz_index["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": target, "title": titles[target]} for target in [project_path, quiz_path])

for source, targets in {
    "devops/multi-region-failover": ["devops/replica-lag-read-contract"],
    "devops/queue-consumer-reliability": ["devops/partition-rebalance-safety"],
    "devops/observability-signals": ["devops/metric-cardinality-budget"],
    "devops/trace-context-propagation": ["devops/trace-sampling-decisions"],
    "devops/ephemeral-environment-controls": ["devops/stuck-finalizer-recovery"],
    "devops/admission-policy-guardrails": ["devops/policy-exception-expiry"],
    "devops/kubernetes-rbac": ["devops/break-glass-access"],
    "devops/incident-response": ["devops/runbook-automation-guardrails"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1,
                  "new_quiz_banks": 1, "total_records": len(rows)}))

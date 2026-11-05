"""Add advanced resilience and security-response DevOps content to local previews."""

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
    "pod-disruption-budgets", "Pod disruption budgets: make node drains measurable",
    "Protect a minimum number of healthy replicas during voluntary eviction without freezing maintenance.",
    "A PodDisruptionBudget (PDB) limits how many matching Pods can be unavailable during voluntary evictions that use the Kubernetes Eviction API. It does not stop a node crash, prevent a deployment from being deleted, or create replacement capacity. Its selector must match the intended workload; a healthy-looking budget attached to zero Pods provides no protection.",
    "A document API runs four replicas and needs three ready during one-node maintenance. Set minAvailable to three, inspect currentHealthy and disruptionsAllowed, and verify replacement Pods can schedule before draining. The manifest is a starting policy for a single namespace. Check that the Deployment template carries the same app label and that the replicas span nodes. If the budget blocks a drain, diagnose unavailable replicas, capacity, and readiness first. Using a forceful deletion to finish a maintenance window bypasses the availability contract. A PDB also does not guarantee zero user errors; validate the client path while a replica leaves service.",
    "yaml", "apiVersion: policy/v1\nkind: PodDisruptionBudget\nmetadata: {name: document-api-budget, namespace: documents}\nspec:\n  minAvailable: 3\n  selector:\n    matchLabels: {app: document-api}",
    "A strict budget can delay node replacement indefinitely when a workload is already unhealthy or spare capacity is missing. Four replicas cost more than one, but the extra instance permits a controlled eviction while maintaining the three-instance floor. Track drain duration and rejected evictions alongside availability; a successful policy is one operators can exercise without bypassing it. Budget health depends on readiness probes, so a false positive readiness check can make the protection misleading.",
    ["Do not assume a PDB protects against node failure.", "Do not set a three-Pod minimum on three replicas and expect an immediate drain.", "Do not bypass the Eviction API to hide an unhealthy workload."],
    ["devops/kubernetes-deployments", "devops/kubernetes-probes", "devops/capacity-load-testing"],
)

lesson(
    "topology-spread-placement", "Topology spread: keep replicas out of one failure domain",
    "Balance Pods across zones or nodes while accounting for capacity and scheduling delay.",
    "A topology spread constraint tells the scheduler how evenly matching Pods should occupy domains such as zones or nodes. The topology key names a node label, the selector identifies the peer Pods, and maxSkew limits the accepted imbalance. With DoNotSchedule, an unsatisfied rule leaves a new Pod pending; ScheduleAnyway expresses a preference and may permit an uneven placement.",
    "A four-replica claims API serves two zones. Start with one zone constraint and inspect node labels before rollout. The sample belongs in a Deployment Pod template, not at the top level of a Deployment. It assumes both zones have enough allocatable CPU and memory. Test a node loss and a zone loss separately: spreading four replicas across zones does not ensure two nodes per zone. Pair placement with resource requests, replica count, a PDB, and traffic routing. If a new revision stays pending, inspect scheduler events and domain eligibility before weakening the rule. Cross-zone calls and storage placement may change latency and network cost.",
    "yaml", "topologySpreadConstraints:\n  - maxSkew: 1\n    topologyKey: topology.kubernetes.io/zone\n    whenUnsatisfiable: DoNotSchedule\n    labelSelector:\n      matchLabels: {app: claims-api}",
    "Hard placement constraints consume headroom because free capacity in one zone cannot always compensate for a full second zone. A label missing from a node changes which domains are eligible. Measure pending time after autoscaler events and during rollout, not only after steady state. A spread rule improves failure isolation but adds scheduling work and may increase cross-zone traffic; the service's recovery goal decides whether that trade is justified.",
    ["Do not use a selector that misses the actual workload label.", "Do not call zone spread a node-level guarantee.", "Do not add DoNotSchedule without checking capacity in every eligible domain."],
    ["devops/pod-disruption-budgets", "devops/kubernetes-resource-budgets", "devops/multi-region-failover"],
)

lesson(
    "graceful-pod-shutdown", "Graceful Pod shutdown: stop accepting work before exit",
    "Drain in-flight requests within a bounded termination period and prove the client behavior.",
    "Graceful shutdown is the coordinated end of a process after a Pod is marked for termination. Kubernetes starts a grace period, runs a preStop hook when configured, and asks the container process to stop; once the deadline expires, remaining processes can be killed. The application must close listeners or mark itself unready, finish bounded work, and acknowledge only operations whose effects are durable.",
    "A receipt API has requests that may take twenty seconds. Give it a measured termination window, handle the stop signal in the server, and stop taking new work before waiting for active handlers. The YAML fragment shows a Pod-level deadline, not the application signal handler. Test a rollout while a slow receipt is in progress. Record whether the client receives a response, whether the write committed, and whether a retry creates a duplicate. Some load balancers observe endpoint changes after a delay; a short fixed sleep in preStop is not a substitute for testing that delay. If a request cannot finish within the window, rely on an idempotent retry or durable queue rather than extending shutdown forever.",
    "yaml", "spec:\n  terminationGracePeriodSeconds: 47\n  containers:\n    - name: receipt-api\n      image: registry.internal/receipt-api@sha256:REPLACE_WITH_FULL_DIGEST\n      ports:\n        - containerPort: 8147",
    "Long grace periods slow rollouts and node maintenance, while short ones interrupt valid work. The number in the fragment is an invented starting value; measure the high percentile of in-flight work and leave room for endpoint propagation. A handler that ignores the stop signal may run until forced termination even when the manifest looks correct. Verify from outside the cluster, since a successful process exit does not prove the user transaction succeeded.",
    ["Do not assume a preStop sleep completes business work.", "Do not acknowledge a queued item before its effect is durable.", "Do not set a grace period without testing the actual application handler."],
    ["devops/pod-disruption-budgets", "devops/queue-consumer-reliability", "devops/kubernetes-probes"],
)

lesson(
    "cronjob-schedule-safety", "CronJob schedule safety: missed runs, overlap, and replay",
    "Make scheduled work idempotent and define what happens when an earlier run is still active.",
    "A Kubernetes CronJob creates Jobs according to a schedule. concurrencyPolicy governs overlap among Jobs created by that same CronJob: Allow runs concurrently, Forbid skips an overlapping start, and Replace terminates the earlier Job. startingDeadlineSeconds limits how late a missed schedule can start. None of those fields turns an external write into an exactly-once operation.",
    "A nightly royalty ledger close runs at 02:17 UTC. Forbid overlap, allow a bounded late start, and give each business date a unique ledger-close key checked by the database. Record the date in durable storage before final publication so a controller restart or manual replay cannot produce a second payout. The fragment assumes the image knows which date to close and has least-privilege credentials supplied outside the manifest. Alert on missed schedules and failed Jobs; a skipped run under Forbid is a business event, not proof that work completed. Test a run that lasts past the next schedule, a controller outage, and a manual retry. Use a time zone explicitly where supported and document daylight-saving behavior if local time matters.",
    "yaml", "apiVersion: batch/v1\nkind: CronJob\nmetadata: {name: royalty-close, namespace: finance}\nspec:\n  schedule: '17 2 * * *'\n  timeZone: Etc/UTC\n  concurrencyPolicy: Forbid\n  startingDeadlineSeconds: 1200\n  jobTemplate:\n    spec:\n      backoffLimit: 2\n      template:\n        spec:\n          restartPolicy: Never\n          containers:\n            - name: royalty-close\n              image: registry.internal/royalty-close@sha256:REPLACE_WITH_FULL_DIGEST",
    "Each Job creates Pods and consumes requested resources even when the business operation later finds nothing to do. Retained Job histories also consume API and log storage; set retention after deciding how failures will be investigated. A narrow deadline can discard important work after a controller outage, while an unbounded catch-up can flood downstream systems. Test the chosen schedule against real processing duration and recovery requirements.",
    ["Do not rely on Forbid as a database lock across separate CronJobs.", "Do not assume every scheduled time produces exactly one Job.", "Do not let a replay pay the same ledger date twice."],
    ["devops/queue-consumer-reliability", "devops/database-change-safety", "devops/alert-design"],
)

lesson(
    "retry-timeout-budgets", "Retries and timeouts: bound the cost of a failed request",
    "Give a request one end-to-end deadline and spend retry capacity deliberately.",
    "A timeout limits how long a caller waits for one operation. A retry attempts the operation again after failure; backoff with jitter spreads those attempts so clients do not hit a recovering dependency in lockstep. Multiple layers of retries can multiply downstream traffic. A transport timeout also cannot tell the caller whether a server committed the write before the connection broke.",
    "A document-signing API calls a remote signer. Give the incoming operation a 2.4-second deadline, reserve time for serialization and response, and allow at most two remote attempts for errors classified as transient. Use a stable idempotency key for the same logical signing request so an uncertain first attempt does not create a second document. The pseudocode is a policy contract, not a library configuration; implement cancellation, error classification, and key persistence in the actual client. Do not retry validation failures or an authorization denial. For a rate limit, honor a trustworthy retry hint only if it fits within the remaining deadline. Observe attempt count, final failure rate, and work performed by the signer; a lower client error rate can hide a dependency being overwhelmed.",
    "text", "Signing request policy\nEnd-to-end deadline: 2400 ms\nRemote attempts: at most 2 total\nAttempt timeout: at most remaining deadline\nRetry only: selected transport failure, 429, transient 5xx\nBackoff: bounded exponential delay with jitter\nWrite identity: stable idempotency key per document request",
    "Two attempts can double load on a sick service. Nested client, proxy, and job retries can multiply that again. Tighter deadlines free resources sooner but may reject work that would have completed; choose them from measured latency and user tolerance. Store idempotency results long enough for the retry horizon and return the original result when the key repeats. A circuit breaker can reject work quickly during a sustained outage but needs its own recovery test.",
    ["Do not retry every error code.", "Do not give each retry a fresh full request deadline.", "Do not treat a timeout as proof that a write did not happen."],
    ["devops/queue-consumer-reliability", "devops/service-level-objectives", "devops/alert-design"],
)

lesson(
    "api-compatibility-window", "API compatibility windows: release consumers and producers safely",
    "Keep old and new clients working while a contract changes across deployments.",
    "An API compatibility window is the period during which a producer supports both the old consumer contract and a new one. It matters when independently deployed services, mobile clients, or retained messages cannot upgrade in one atomic step. A field addition may be safe for tolerant consumers, but changing its meaning, removing an enum value, or making a previously optional field mandatory can still break a client.",
    "A shipment service adds a delivery-window field. First publish a contract fixture with the field optional; deploy a producer that emits it while preserving the old response. Run consumer contract tests against actual supported client versions and replay retained queue messages through the new reader. Then upgrade consumers. Only after usage shows old clients have left the support window should the producer make a breaking change on a new versioned route. The JSON fragment is a representative response, not a full schema. Record the date the old contract stops being supported and which team owns each client. A database expand-and-contract migration should follow the same overlap, because an application rollback may read rows written by the newer release.",
    "text", "GET /shipments/SH-473\n200 OK\n{\"shipmentId\":\"SH-473\",\"state\":\"in_transit\",\"deliveryWindow\":{\"start\":\"2026-10-04T09:00:00Z\",\"end\":\"2026-10-04T12:00:00Z\"}}",
    "Supporting two contracts increases code, storage, and test combinations. Track client-version traffic and queue retention so the window ends on evidence rather than a calendar guess. Contract tests are fast but cannot prove production clients behave correctly with every optional value; monitor deserialization failures and user operations during rollout. Permanent compatibility shims impose a recurring maintenance cost, so retire the old path through a planned version change.",
    ["Do not make a new response field required for old clients.", "Do not delete the old parser while retained messages still exist.", "Do not assume an application rollback restores the former database shape."],
    ["devops/database-change-safety", "devops/progressive-delivery", "devops/feature-flag-release"],
)

lesson(
    "container-runtime-restrictions", "Container runtime restrictions: remove privileges a service does not use",
    "Test a narrow security context against the service's real file and syscall needs.",
    "A Kubernetes security context controls privileges and access for a Pod or container. Running as a non-root user, disallowing privilege escalation, dropping Linux capabilities, using a read-only root filesystem, and selecting a seccomp profile reduce what compromised code can do. They do not repair a vulnerable dependency or make a leaked credential harmless.",
    "An invoice renderer writes temporary PDFs to a mounted scratch directory, not to its image filesystem. Start the container with the restrictive settings below in a test namespace, then exercise font loading, temporary file creation, and a full PDF render. The fragment belongs inside one container specification and assumes its image can run with the selected user ID. Grant a bounded writable volume only for the scratch path; do not reopen the entire root filesystem because one library expects a cache directory. Confirm that the service account token is unnecessary and disable its automatic mount when possible. Test on the runtime used in production because the RuntimeDefault seccomp profile can differ by container runtime.",
    "yaml", "securityContext:\n  runAsNonRoot: true\n  runAsUser: 10473\n  allowPrivilegeEscalation: false\n  readOnlyRootFilesystem: true\n  capabilities:\n    drop: [ALL]\n  seccompProfile:\n    type: RuntimeDefault",
    "Restrictive settings can expose hidden writes and syscall dependencies during migration. That test work is cheaper than discovering them during an incident rollout, but it needs representative rendering inputs. A read-only image may shift temporary data into memory-backed storage, which still consumes node resources. Watch memory and ephemeral storage after the change. Runtime restrictions are one layer; image provenance, network policy, RBAC, and secret handling remain separate controls.",
    ["Do not add privileged mode to fix one missing cache directory.", "Do not assume runAsNonRoot proves the image is safe.", "Do not omit application tests on the actual container runtime."],
    ["devops/admission-policy-guardrails", "devops/network-policy-isolation", "devops/kubernetes-rbac"],
)

lesson(
    "cluster-upgrade-drill", "Cluster upgrade drill: preserve a path through each version step",
    "Test workload eviction and API compatibility before moving control-plane or node versions.",
    "A Kubernetes cluster upgrade changes API server, controllers, kubelets, add-ons, and sometimes the container runtime at different times. The supported version skew between components constrains the order of operations; the exact rule depends on the versions and distribution in use. A successful control-plane upgrade does not prove that applications survive node replacement or that old manifests still apply.",
    "For a two-zone claims cluster, inventory deprecated APIs and controller versions, then rehearse the target version in a test cluster with representative workloads. Check PDB disruptionsAllowed and spare placement capacity before draining each node. Upgrade the control plane using the provider-supported path, then move one node pool at a time while watching request errors, pending Pods, storage attach, and ingress routes. The runbook outline is deliberately provider-neutral; use the distribution's procedure for the actual command sequence. If an add-on fails, stop before advancing another pool. Recreate a node from a known image when required; do not assume a control-plane downgrade is supported. Keep a service-level recovery plan for workloads that cannot roll back their infrastructure in place.",
    "text", "Claims cluster upgrade gate\n1. Record current and target versions and supported skew.\n2. Inventory removed APIs and add-on compatibility.\n3. Rehearse control plane plus one node pool in test.\n4. Check PDBs, zone headroom, backups, and user-path probes.\n5. Upgrade one production pool; measure errors and pending Pods.\n6. Stop or proceed on the recorded service thresholds.",
    "Extra node-pool capacity and a test cluster cost money during the upgrade window. Without them, a drain can stall or evict more useful capacity than the application tolerates. Cluster control-plane health, workload availability, and data integrity need separate gates. Version-skew guidance can change between releases, so review the target release's current support policy and provider limits when scheduling the work.",
    ["Do not drain nodes before checking PDBs and placement headroom.", "Do not treat a green control plane as proof that user requests work.", "Do not assume the cluster can be downgraded after a failed upgrade."],
    ["devops/pod-disruption-budgets", "devops/topology-spread-placement", "devops/backup-and-recovery"],
)

lesson(
    "log-pipeline-retention", "Log pipelines: preserve incident evidence without ingesting secrets",
    "Set a bounded log schema, retention window, and loss signal before scaling collection.",
    "A log pipeline moves application events from processes through a collector to storage and search. It can fail at the producer, collector, transport, or index. Structured records help correlate a request across services, but logging every payload creates cost and privacy exposure. A log search result is incomplete unless the pipeline's loss and delay are understood.",
    "A claims API writes one JSON event for a failed claim submission with request ID, stable error code, and deployment revision. It excludes claimant names, document contents, tokens, and payment data. The sample is one record to test parsing and redaction, not a logging-library configuration. Sample routine successes if volume demands it, but retain actionable errors under a clear policy. Alert on collector queue depth, dropped records, and end-to-end ingest delay. Test a storage outage: the application should have a bounded logging path rather than blocking every request indefinitely. Give incident responders enough retention to investigate an event, and restrict access to logs that still contain operational identifiers.",
    "text", "{\"timestamp\":\"2026-10-01T08:17:23Z\",\"service\":\"claims-api\",\"revision\":\"claims-047\",\"requestId\":\"req-6c49\",\"event\":\"claim_submit_failed\",\"errorCode\":\"DOCUMENT_TIMEOUT\"}",
    "Ingest volume grows with event rate and fields, while indexing high-cardinality values increases storage and query cost. Retaining every debug event for months can crowd out the incidents that matter. Dropping logs during collector pressure may preserve application availability but removes evidence; count and alert on that loss. Apply deletion and access controls to archived copies as well as the active index. A trace can add context, but it does not replace a durable business event record.",
    ["Do not log credentials or full customer documents.", "Do not treat a quiet log search as proof that no error occurred.", "Do not let synchronous logging stall a critical request indefinitely."],
    ["devops/observability-signals", "devops/trace-context-propagation", "devops/incident-response"],
)

lesson(
    "credential-incident-rotation", "Credential incident response: revoke access before rebuilding trust",
    "Inventory exposure, contain active access, and prove replacement credentials work.",
    "Credential rotation replaces an authentication secret or key. In an incident, the operation also requires containment: identify where the old credential was used, revoke or disable it, remove copies from accessible stores, and check for unauthorized actions. Issuing a second credential while the first remains valid does not end the exposure.",
    "A CI deploy token appears in a public build log. Pause the affected deployment workflow, revoke the token at its issuer, and inspect audit logs for use since the earliest likely exposure. Create a scoped replacement with a shorter lifetime and store it in the approved secret manager; use it only after its permissions and target environment are verified. The text block is an incident checklist, not a shell script. Rotate downstream credentials if the token could retrieve them. Remove the log from public access according to the platform's retention process, but do not mistake deletion for revocation; copies may exist. Resume the pipeline through a test deployment and monitor for denied requests using the old identity. Record owners, timestamps, evidence preserved, and the reason the incident is closed.",
    "text", "Deploy-token exposure response\nContain: pause workflow and revoke token at issuer\nScope: identify permission set, use history, and reachable secrets\nReplace: issue least-privilege short-lived identity\nVerify: test a nonproduction deployment and old-token denial\nRecover: resume release flow with audit monitoring\nRecord: timeline, affected artifacts, owners, and follow-up",
    "Revocation can interrupt releases until a replacement is installed; plan a break-glass path whose use is audited and time-limited. Broad credential reuse makes scoping slower and increases the number of systems to inspect. Moving to workload identity or short-lived federation reduces standing-secret rotation work, but the trust policy itself still needs review. A clean test deployment verifies function, not the absence of unauthorized historical use; audit evidence remains necessary.",
    ["Do not only remove a leaked log while keeping the token active.", "Do not reuse the same credential across test and production.", "Do not declare recovery before testing old-token denial."],
    ["devops/github-actions-security", "devops/secrets-and-configuration", "devops/incident-response"],
)


titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/resilience-game-day-project"
quiz_path = "quizzes/devops-resilience-and-response"
titles[project_path] = "Project: run a service resilience game day"
titles[quiz_path] = "DevOps resilience and response decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


groups = [
    ("Availability during maintenance", "Preserve service capacity while nodes and Pods leave the cluster.", ["pod-disruption-budgets", "topology-spread-placement", "graceful-pod-shutdown", "cluster-upgrade-drill"]),
    ("Bounded background and remote work", "Give schedules, retries, and contract changes explicit failure behavior.", ["cronjob-schedule-safety", "retry-timeout-budgets", "api-compatibility-window"]),
    ("Runtime evidence and response", "Restrict containers, retain useful signals, and close credential exposure.", ["container-runtime-restrictions", "log-pipeline-retention", "credential-incident-rotation"]),
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
               category="DevOps", difficulty="Advanced", tags=["devops", "resilience"],
               sort_order=17800 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Rehearse a node drain, a timed-out write, and a credential leak in a disposable service.",
               difficulty="Advanced", sort_order=17890,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in ["devops/pod-disruption-budgets", "devops/graceful-pod-shutdown", "devops/retry-timeout-budgets", "devops/credential-incident-rotation"]]}
project["body"] = (
    "<p>A resilience game day is a controlled exercise that tests whether a service meets a stated user and recovery objective during planned faults. Use a disposable two-zone environment, synthetic claims, and credentials created only for the exercise. State the expected transaction success rate, maximum request latency, and incident response clock before changing the system.</p>"
    "<h2>Prepare the system</h2><p>Run four claims API replicas with a PDB that needs three ready, spread them across zones, and implement bounded graceful shutdown. Give the API a stable idempotency key for a claim submission. Record the image digest, the current deployment revision, the synthetic claim IDs, and how to reset the environment. Install a log-loss signal and a client-side user-path probe. Do not use a real production token as the credential-leak prop.</p>"
    "<pre><code class=\"language-text\">Claims game-day record\nScenario A: drain one node while a slow request is in flight\nScenario B: cut signer response after commit; retry same claim key\nScenario C: expose disposable CI token in private test log\nEvidence: PDB status, client result, claim count, token denial\nStop gate: user error threshold or unexpected data write\nOwner: named operator and observer</code></pre>"
    "<h2>Run and recover</h2><p>Drain one node through the Eviction API and watch both PDB status and client errors. Interrupt the remote signer after a durable write, retry with the same idempotency key, and verify that only one claim was created. Place the disposable token in a restricted test log, then revoke it at the issuer, test old-token denial, create a scoped replacement, and resume one test deployment. Stop immediately if the exercise creates unexpected writes or loses visibility. Capture actual recovery times and every manual decision, including a stalled drain.</p>"
    "<h2>Cost and verification</h2><p>The exercise consumes temporary cluster capacity, log storage, and operator time. That cost buys direct evidence about the system's failure path, but only for the conditions actually tested. Record whether the PDB allowed eviction, whether the client received one durable result, whether the old token failed, and which observation was missing. Remove disposable resources and credentials after preserving the approved evidence.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not call a successful drain a user-path test.</li><li>Do not infer idempotency from a single request without an uncertain first result.</li><li>Do not remove a leaked test log in place of revoking its token.</li></ul>"
    "<h2>Reference lessons</h2>" + links(["devops/pod-disruption-budgets", "devops/topology-spread-placement", "devops/graceful-pod-shutdown", "devops/retry-timeout-budgets", "devops/credential-incident-rotation", project_hub]))
rows.append(project)
project_index = by_path[project_hub]
project_index["data"]["modules"][0]["lessons"].append(project_path)
project_index["body"] += "<h2>Resilience game day</h2>" + links([project_path])
project_index["updated_at"] = stamp

questions = [
    ("Which disruption does a PDB constrain?", ["Voluntary eviction through the Eviction API", "A physical node failure", "A direct Deployment deletion"], 0, "A budget protects the supported voluntary eviction path."),
    ("What can DoNotSchedule cause when one zone is full?", ["A pending replacement Pod", "Automatic cross-zone capacity creation", "A successful user request"], 0, "The scheduler cannot ignore a hard spread rule."),
    ("What must the application do during Pod termination?", ["Stop accepting new work and finish bounded in-flight work", "Only increase replica count", "Delete the PDB"], 0, "The manifest alone cannot drain an application handler."),
    ("What does CronJob Forbid control?", ["Overlapping Jobs from that same CronJob", "All jobs in a namespace", "Exactly-once database writes"], 0, "Business idempotency needs its own key or constraint."),
    ("What does a client timeout prove about a write?", ["Only that the caller stopped waiting", "That the server rolled back", "That no database row exists"], 0, "The server may commit before a response is lost."),
    ("When may the old API reader be removed?", ["After supported clients and retained messages no longer need it", "When the new producer first deploys", "When one contract test passes"], 0, "A compatibility window ends on observed consumer and retention evidence."),
    ("What does readOnlyRootFilesystem still permit when configured?", ["Writes to an explicitly mounted volume", "Unrestricted writes to the image root", "Proof of safe dependencies"], 0, "Writable volumes need their own scope and limits."),
    ("What should precede a production node-pool upgrade?", ["Check version skew, PDBs, add-ons, and spare capacity", "Delete all backups", "Assume control-plane health covers users"], 0, "An upgrade affects several independent service paths."),
    ("What does an empty log search prove during collector loss?", ["Nothing about whether the application had errors", "That all requests succeeded", "That retention is sufficient"], 0, "The pipeline can drop or delay records."),
    ("What ends a leaked token's ability to authenticate?", ["Revocation or disablement at its issuer", "Deleting one visible log line", "Changing the token's description"], 0, "Copies can remain after a log is removed."),
    ("What should a drain exercise measure?", ["Client outcome and replacement readiness", "Only kubectl exit status", "Only node CPU temperature"], 0, "Maintenance succeeds when the service still meets its objective."),
    ("What prevents duplicate effects after an uncertain remote write?", ["A stable idempotency key enforced at the effect boundary", "A longer client timeout alone", "A fresh key on every retry"], 0, "Repeated attempts must resolve to the same logical operation."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on maintenance, retries, schedules, upgrades, and credential response.",
            sort_order=17900, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in ["devops/pod-disruption-budgets", "devops/cronjob-schedule-safety", "devops/retry-timeout-budgets", "devops/cluster-upgrade-drill", "devops/credential-incident-rotation"]],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(answer - index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, answer, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the operational decision that survives a real failure, then review the associated lesson when a result is unclear.</p><h2>Review these lessons</h2>" + links([item["path"] for item in quiz["data"]["related"]]) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-delivery", "quizzes/devops-operations", "quizzes/devops-platform-reliability", "quizzes/devops-advanced-delivery"]) + "<h3>Common Mistakes</h3><ul><li>Do not confuse a configured guardrail with a measured user outcome.</li><li>Do not confuse timeout with a rolled-back write.</li></ul>"
rows.append(quiz)
quiz_index = by_path[quiz_hub]
quiz_index["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_index["body"] += "<h2>Resilience and response check</h2>" + links([quiz_path])
quiz_index["updated_at"] = stamp

for source, targets in {
    "devops/kubernetes-deployments": ["devops/pod-disruption-budgets", "devops/graceful-pod-shutdown"],
    "devops/kubernetes-resource-budgets": ["devops/topology-spread-placement"],
    "devops/queue-consumer-reliability": ["devops/cronjob-schedule-safety", "devops/retry-timeout-budgets"],
    "devops/database-change-safety": ["devops/api-compatibility-window"],
    "devops/admission-policy-guardrails": ["devops/container-runtime-restrictions"],
    "devops/pod-disruption-budgets": ["devops/cluster-upgrade-drill"],
    "devops/observability-signals": ["devops/log-pipeline-retention"],
    "devops/github-actions-security": ["devops/credential-incident-rotation"],
}.items():
    row = by_path.get(source) or next(row for row in rows if row["path"] == source)
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1,
                  "new_quiz_banks": 1, "total_records": len(rows)}))

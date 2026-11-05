"""Extend the DevOps curriculum with cross-system operational boundaries."""

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
                      practice=practice, language=language, sample=sample, cost=cost,
                      mistakes=mistakes, related=related))


lesson(
    "mesh-identity-boundaries", "Mesh identity: require encrypted peers and narrow service access",
    "Distinguish workload authentication from authorization and test both sides of a mesh policy.",
    "Service-mesh mutual TLS authenticates workloads at the proxy boundary and encrypts traffic between participating proxies. Strict peer authentication rejects plaintext inbound traffic for the selected scope. It does not, by itself, say which authenticated service may call another; an authorization policy supplies that decision. A workload outside the mesh, a bypassed port, or a mismatched identity can still defeat an assumed trust path.",
    "A claims API should accept calls from a settlement worker, but not a report renderer. Apply the policy fragment to a disposable namespace after confirming proxy injection and the actual service-account names. This example contains two resources; production rollout should stage and observe each one separately. First require strict mutual TLS for the selected workload. Then allow only the settlement service account to call the claims API. Verify an authorized request succeeds and an equally valid mesh peer with the renderer identity is denied. Also try a plaintext request. A failed denial is a stop condition, even when ordinary application tests pass. Check control-plane policy distribution before blaming the application. During rotation or migration, list the exact old and new identities and remove the old rule after the transition.",
    "yaml", "apiVersion: security.istio.io/v1\nkind: PeerAuthentication\nmetadata: {name: claims-peers, namespace: claims}\nspec:\n  selector:\n    matchLabels: {app: claims-api}\n  mtls: {mode: STRICT}\n---\napiVersion: security.istio.io/v1\nkind: AuthorizationPolicy\nmetadata: {name: claims-callers, namespace: claims}\nspec:\n  selector:\n    matchLabels: {app: claims-api}\n  action: ALLOW\n  rules:\n  - from:\n    - source:\n        principals: [cluster.local/ns/claims/sa/settlement-worker]",
    "Proxies consume CPU and memory and add a network hop; policy evaluation also creates an operational dependency on identity issuance and configuration delivery. An allow rule for one principal can deny legitimate batch or health traffic that used another identity, so inventory callers before enforcement. Measure request failure by source identity and route, then compare it with an authorized synthetic transaction. Do not treat encryption as proof that the caller was permitted or that application data was valid.",
    ["Do not equate strict peer authentication with an allowlist.", "Do not turn on a narrow allow rule before cataloging actual service accounts.", "Do not accept a passing allowed-call test without a denied-call test."],
    ["devops/network-policy-isolation", "devops/service-account-token-boundaries", "devops/secrets-and-configuration", "devops/egress-dns-contract"],
)

lesson(
    "database-pool-pressure", "Database pool pressure: bound waiting before the database collapses",
    "Size connection demand across replicas and shed excess work at the application edge.",
    "A database connection pool bounds the number of concurrent database sessions an application instance can hold. When every session is busy, another request waits for a release or times out. The pool protects the database only if the sum across all replicas, workers, and administrative clients fits the database session budget; a per-Pod maximum alone is not a system limit.",
    "A claims service has twelve API replicas, each configured for eighteen database connections, and four workers with eight each. That is 248 possible application sessions before migrations and operator access. If the database allows 260 sessions, the margin is too small for a rollout that temporarily adds replicas. Allocate an explicit connection budget per workload, reserve administrator access, and load-test while the rollout reaches peak Pod count. The text contract is a capacity review record; apply the selected values in the actual pool library and deployment configuration. Set a finite acquisition timeout shorter than the end-to-end request budget. Observe active, idle, pending, and timed-out acquisitions alongside database CPU, lock waits, and query duration. A larger pool can make contention worse when slow queries or locks are the cause. Fix the query or admission rate before raising the maximum.",
    "text", "Claims database session budget\nDatabase ceiling: 260 sessions\nAPI: 12 replicas x 18 = 216\nWorkers: 4 replicas x 8 = 32\nApplication peak before surge: 248\nReserve for rollout, migration, and operators: insufficient\nDecision: lower per-instance caps or raise tested database capacity",
    "A small pool limits database concurrency but adds queue time at the application. A large pool reduces short waits until the database saturates, then increases lock contention and memory per session. Pool acquisition timeout is a user-visible failure boundary; it should trigger a controlled response rather than an unbounded retry that holds more request threads. Recalculate after every replica or worker change, and use the peak rollout replica count rather than only steady state.",
    ["Do not multiply a per-instance pool size by only the steady-state replica count.", "Do not raise the pool maximum to hide slow queries or locks.", "Do not set pool acquisition timeout beyond the request deadline."],
    ["devops/capacity-load-testing", "devops/horizontal-autoscaling", "devops/database-change-safety", "devops/retry-timeout-budgets"],
)

lesson(
    "node-pressure-eviction", "Node pressure eviction: trace lost Pods to exhausted local resources",
    "Separate kubelet eviction from application crashes and plan capacity for both memory and disk.",
    "Node-pressure eviction is a kubelet response to scarce node resources such as available memory or filesystem space. The kubelet may reclaim local resources and then terminate Pods when configured thresholds remain crossed. Pod requests, actual use, and priority affect which Pods are candidates. A PodDisruptionBudget does not prevent this involuntary termination, so an apparently safe maintenance budget is not a node-capacity plan.",
    "A document-index worker disappears during a large image rollout. Inspect Pod termination reason, node conditions, events, and filesystem usage before restarting it. The commands are read-only; run them in the affected cluster context. If ephemeral storage is full, find whether image layers, writable container data, or logs consumed it. Set realistic ephemeral-storage requests and limits, and give the node room to pull the next image before draining another node. If memory pressure caused the eviction, distinguish container OOM from node-level eviction and check whether request values reflect observed working sets. Moving the worker to another full node only shifts the incident. Verify replacement Pods process a synthetic document and that queue age falls after capacity is restored.",
    "bash", "kubectl get pod -n indexing -o wide\nkubectl describe pod -n indexing document-index-worker-0\nkubectl describe node worker-node-47\nkubectl get events -n indexing --sort-by=.lastTimestamp",
    "Keeping free node memory and disk has a direct compute cost, but a zero-headroom cluster pays through failed image pulls, evictions, and slower recovery. Tight limits can terminate healthy bursts; missing requests invite unsafe packing. Track node resource pressure and Pod eviction counts with the user-facing queue age. Do not infer an application regression solely from a restart count, and do not call an eviction solved until node pressure and replacement capacity are both understood.",
    ["Do not expect a disruption budget to block node-pressure eviction.", "Do not treat every terminated Pod as an application OOM.", "Do not ignore image and log disk use when sizing ephemeral storage."],
    ["devops/kubernetes-resource-budgets", "devops/pod-disruption-budgets", "devops/namespace-resource-quotas", "devops/queue-consumer-reliability"],
)

lesson(
    "node-autoscaling-headroom", "Node autoscaling: make pending Pods schedulable before traffic rises",
    "Connect workload scaling to real node constraints and a measured provisioning delay.",
    "A node autoscaler provisions or removes nodes in response to unschedulable Pods and configured node constraints. It cannot create capacity for a Pod whose requests, topology rules, volume limits, or node selectors have no compatible node type. Workload autoscaling and node autoscaling act on different signals and time scales; more desired replicas do not mean immediately available service capacity.",
    "A parcel API scales from six to fifteen replicas during a promotion. Model the peak request footprint, including one surge replica per rollout slice, then check that at least one permitted node type can fit each pending Pod. The command sequence is a diagnostic read, not an autoscaler installation. Inspect scheduling events for the first Pending Pod, node-pool upper bounds, topology spread, and storage attachment limits. Measure the time from a Pending Pod to a Ready endpoint under a controlled load ramp. If provisioning takes several minutes, keep minimum spare capacity or pre-scale before a known event. Confirm that the ingress and database can support the added replicas; otherwise the autoscaler only moves the bottleneck. Test scale-down separately so draining does not violate a stateful application's availability rule.",
    "bash", "kubectl get pods -n parcels --field-selector=status.phase=Pending\nkubectl describe pod -n parcels parcel-api-pending-47\nkubectl get nodes -L topology.kubernetes.io/zone\nkubectl get events -n parcels --sort-by=.lastTimestamp",
    "Spare nodes cost money while idle, but cold provisioning adds latency and may fail during provider capacity shortages. Under-requesting resources makes scaling appear cheaper until contention or eviction hits. Over-requesting can make otherwise healthy Pods unschedulable. Record scale-out lead time and compare it with the service's tolerated demand spike. Readiness after scheduling still depends on image pulls, startup, and downstream availability.",
    ["Do not assume a Pending Pod will trigger a node that can satisfy impossible affinity.", "Do not treat desired replicas as available endpoints.", "Do not tune only CPU scaling while database sessions remain fixed."],
    ["devops/horizontal-autoscaling", "devops/node-pressure-eviction", "devops/namespace-resource-quotas", "devops/database-pool-pressure"],
)

lesson(
    "event-schema-evolution", "Event schema evolution: release consumers before new event shapes",
    "Check compatibility against retained history and keep business meaning separate from syntax.",
    "An event schema is the wire contract shared by producers and consumers. A compatibility check can establish whether a reader can decode another schema version, but it cannot prove that business meaning stayed the same. Backward compatibility concerns a new consumer reading older events; forward compatibility concerns an older consumer reading newer events. Nontransitive checks may compare only with the immediately previous version, which is insufficient when consumers replay a long-lived topic.",
    "A settlement stream adds an optional reconciliation code to payout events. Inventory consumers and the topic's retention window before producing that field. If old consumers must continue reading new events, select a compatibility rule that covers that direction and test old binaries against new messages. If a new consumer may replay events from the first retained revision, test against all retained schemas or use a transitive rule that fits the format. The text block is an approval contract, not a registry API request. Deploy consumers that tolerate the new field first, then the producer. Preserve an unknown-field behavior test and a business invariant: a missing reconciliation code must not silently mean the payout was approved. Run a replay sample before removing an old field; lagging consumers and dead-letter events may outlive the deployment window.",
    "text", "Payout event change gate\nField: reconciliation_code, optional on the wire\nOld producer -> new consumer: verified against retained versions\nNew producer -> old consumer: verified for active readers\nBusiness rule: absent value is not approval\nReplay: oldest retained event decoded and processed\nRemove old field only after consumer and retention inventory",
    "Registry checks add build time and version-management work but prevent many decode failures. A permissive rule can allow semantic breakage, while an overly strict rule can block safe additions. Retaining old consumers or dual fields uses engineering time and payload space. Track decode errors, consumer lag, and business-effect mismatches separately. A release that passes a schema check but sends the wrong amount is still a failed release.",
    ["Do not call a syntactic compatibility pass a business-contract proof.", "Do not test only the newest prior version when replay spans older data.", "Do not delete a field while a retained consumer still requires it."],
    ["devops/api-compatibility-window", "devops/dead-letter-replay", "devops/queue-consumer-reliability", "devops/database-backfill-checkpoints"],
)

lesson(
    "dns-cutover-safety", "DNS cutovers: budget for resolver caches and mixed destinations",
    "Move an endpoint while old cached answers remain valid and verify from outside the cluster.",
    "A DNS cutover changes a record that maps a name to a target. Recursive resolvers can continue serving a previously cached answer until its time to live expires, so one successful lookup against an authoritative server does not mean every client has moved. Clients and intermediaries may also keep established connections after a new lookup would return the new destination.",
    "A claims endpoint moves to a new edge provider. Lower the existing record's TTL ahead of the cutover and wait at least the prior TTL before relying on the lower value. Prepare both old and new backends to serve compatible requests during the overlap. The shell sample reads a public name through two recursive resolvers and checks the TLS handshake; it does not alter DNS or verify the application response. Record the authoritative answer, resolver answers, certificate, route, and a user transaction from outside the cluster. Keep the old destination healthy through the cache window and connection-drain period. If the new route fails, restoring the previous record does not instantly move clients back; the new answer may also be cached. Confirm the domain's delegated name servers point to the zone you edited before declaring a propagation incident.",
    "bash", "dig claims.aitrove.test A @1.1.1.1\ndig claims.aitrove.test A @8.8.8.8\nopenssl s_client -connect claims.aitrove.test:443 -servername claims.aitrove.test -verify_return_error </dev/null",
    "A short TTL increases resolver traffic and can make an emergency change appear quicker, but it cannot erase values already cached under the old TTL. Maintaining two serving destinations costs extra compute and coordination. DNS health is not application health: a correct address may lead to an invalid certificate or a broken write path. Measure a real external transaction and continue watching both destinations until old connections have drained.",
    ["Do not lower TTL at the exact cutover and expect old caches to forget their answer.", "Do not shut down the old endpoint as soon as the authoritative record changes.", "Do not treat one resolver response as global propagation proof."],
    ["devops/dns-tls-edge", "devops/egress-dns-contract", "devops/progressive-delivery", "devops/synthetic-transaction-monitoring"],
)

lesson(
    "ci-deployment-concurrency", "CI deployment concurrency: serialize mutations without losing change evidence",
    "Use a deployment lock that preserves completed checks and makes cancellation behavior explicit.",
    "CI concurrency groups limit how many workflow runs or jobs in the same group execute at once. They are useful for serializing changes to one environment, but cancellation settings matter: replacing a pending run can skip an intermediate deployment, and canceling a running deployment can interrupt a mutation after some resources have changed. A passing status check applies to a particular commit and workflow result, not to every later commit on the branch.",
    "A parcel API deploys from a protected branch. Keep build and test jobs tied to each commit, and place the production deployment job in a group unique to that environment. The YAML fragment belongs under a job, not at the workflow root. It avoids canceling a running deployment, but the team's queue behavior still needs review in its current CI configuration. Require checks and the deployment approval rule appropriate to the repository. After each run, read back the deployed image digest and attach it to the exact commit. Re-run required checks when the merge base changes under a merge queue; do not carry forward a green result from a stale head. If a queued run is replaced, record which commit was skipped and verify that the final artifact includes its intended change. A lock does not make infrastructure changes atomic.",
    "yaml", "concurrency:\n  group: parcel-api-production-deploy\n  cancel-in-progress: false\nenvironment: production\nsteps:\n  - name: Deploy reviewed image\n    run: ./scripts/deploy-reviewed-digest.sh",
    "Serializing deployments increases queue time but reduces races between two writers to the same environment. A single broad group can block unrelated services, so scope it to the actual shared resource. A cancelled run may leave its build artifact intact while its deployment state is partial. Examine CI history, deployment-controller state, and the running digest before retrying. Branch protection and deployment concurrency solve separate problems: one gates a merge, the other orders environment mutations.",
    ["Do not use one concurrency group for unrelated environments.", "Do not cancel an in-progress stateful deployment without a recovery plan.", "Do not equate a green check on an older commit with proof of the deployed digest."],
    ["devops/continuous-integration", "devops/github-actions-security", "devops/artifact-promotion", "devops/release-evidence-record"],
)

lesson(
    "synthetic-transaction-monitoring", "Synthetic transactions: measure the route a user actually takes",
    "Probe from outside the system and separate transport success from business success.",
    "A synthetic transaction is a controlled request that exercises a service path before a customer reports failure. A network or HTTP probe can confirm reachability, TLS, response status, and latency; it cannot prove an order or payout completed unless it performs and verifies that business operation. The probe's location, credentials, data, and cleanup determine what failure it can detect.",
    "A claims service exposes a health endpoint that stays green during a database write outage. Run an external HTTP probe for TLS and route availability, then a separate synthetic claim using a dedicated low-privilege test identity and a reversible or isolated record. The PromQL expression checks the external probe's success signal; the business transaction requires its own metric and verification. Place at least one probe outside the cluster and label each target by stable service and region, without customer IDs. Alert on sustained failure and attach the last successful transaction time to the incident. Expire test credentials like any other secret and clean synthetic records under a named retention rule. A probe that only calls the same internal load balancer as the application misses public DNS and edge faults.",
    "promql", "min_over_time(probe_success{job=\"claims-external-http\"}[5m]) == 0",
    "External probes create small but recurring traffic, storage, and notification cost. A single probe location may report a local network fault as a global outage; several locations add expense and interpretation work. A test write can have real side effects if isolation is weak, so scope it to a dedicated account and verify cleanup. The query detects five minutes of continuous probe failure for each target; a complete alert also handles absent series and separates transport failure from business-operation failure.",
    ["Do not call a green health endpoint proof of successful writes.", "Do not use production customer credentials for synthetic transactions.", "Do not alert on probe failure without checking missing metric series and probe location."],
    ["devops/observability-signals", "devops/slo-burn-rate-alerts", "devops/dns-cutover-safety", "devops/incident-response"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/cross-system-release-project"
quiz_path = "quizzes/devops-system-boundaries"
titles[project_path] = "Project: release across identity, capacity, DNS, and events"
titles[quiz_path] = "DevOps system boundaries decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


groups = [
    ("Trust and shared-resource limits", "Authenticate peers and budget database sessions across replicas.", ["mesh-identity-boundaries", "database-pool-pressure"]),
    ("Node and event boundaries", "Trace involuntary evictions, delayed capacity, and retained message contracts.", ["node-pressure-eviction", "node-autoscaling-headroom", "event-schema-evolution"]),
    ("External release evidence", "Control DNS overlap, deployment order, and user-path probes.", ["dns-cutover-safety", "ci-deployment-concurrency", "synthetic-transaction-monitoring"]),
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
               sort_order=18400 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Rehearse an external cutover while workload identity, pool capacity, and event compatibility change.",
               difficulty="Advanced", sort_order=18490,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project_related = ["devops/mesh-identity-boundaries", "devops/database-pool-pressure", "devops/node-autoscaling-headroom", "devops/event-schema-evolution", "devops/dns-cutover-safety", "devops/synthetic-transaction-monitoring"]
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>This exercise releases a synthetic claims service across several boundaries that cannot be verified by one controller. Use disposable infrastructure, test identities, and isolated records. Record the current image digest, active event schemas, DNS TTL, database session ceiling, and an external transaction baseline before the release.</p>"
    "<h2>Prepare the overlap</h2><p>Stage a mesh allow policy for the settlement worker and deny the report renderer in a test namespace. Calculate the maximum database sessions at peak rollout replicas, including workers and administrator reserve. Produce an optional event field only after both current and oldest-retained message versions pass reader tests. Lower DNS TTL ahead of the cutover, and keep both edge destinations available through the cache window. Serialize production mutations under a deployment group; preserve the commit-to-digest record for every completed run.</p>"
    "<pre><code class=\"language-text\">Claims release gate\nMesh: allowed and denied identity probes recorded\nCapacity: pool sum at peak replicas plus operator reserve\nEvents: old and new readers tested on retained data\nDNS: old TTL elapsed before target change\nExternal: TLS probe and synthetic write both pass\nStop: named owner returns traffic without losing evidence</code></pre>"
    "<h2>Inject failure and recover</h2><p>Make one node unable to host a requested Pod and inspect its scheduling event; do not assume the autoscaler will repair impossible affinity. Saturate the database pool with bounded synthetic load and confirm acquisition timeout occurs before the request deadline. Switch the DNS target to a route that answers health checks but fails the synthetic write. Roll back traffic while keeping the prior endpoint alive, and observe cached answers from two resolvers. Confirm the old image can still read the new optional event field before declaring rollback complete.</p>"
    "<h2>Cost and verification</h2><p>Record extra proxy, node, edge, and database capacity used during the overlap. Capture session waits, Pending-Pod duration, resolver answers, identity denials, and successful synthetic writes. The controller's Ready state is one signal; the release decision needs user-path evidence. Clean test records and identities only after the evidence and recovery checks are retained under the team's policy.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not use one successful DNS lookup as proof that all clients moved.</li><li>Do not count desired replicas as available capacity.</li><li>Do not call a passing mesh handshake permission to perform every operation.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub]))
rows.append(project)
project_index = by_path[project_hub]
project_index["data"]["modules"][0]["lessons"].append(project_path)
project_index["body"] += "<h2>Cross-system release exercise</h2>" + links([project_path])
project_index["updated_at"] = stamp

questions = [
    ("What does strict mesh peer authentication prove?", ["A participating peer used authenticated encrypted traffic", "Every authenticated caller is authorized", "Every business request is valid"], 0, "Peer authentication and application authorization are separate decisions."),
    ("What matters when sizing database connections?", ["Peak sessions across all replicas and workers", "Only the maximum on one Pod", "Only idle connections on the quietest day"], 0, "A database sees the aggregate session demand."),
    ("Can a disruption budget stop a node-pressure eviction?", ["No, it does not block involuntary resource-pressure termination", "Yes, all terminations are denied", "Only if the Pod has no request"], 0, "Pressure eviction and voluntary disruption use different paths."),
    ("What should be inspected when a scaled Pod stays Pending?", ["Scheduling constraints and compatible node capacity", "Only the image registry", "Only the application's HTTP logs"], 0, "A node cannot be provisioned to satisfy impossible constraints."),
    ("What does backward event-schema compatibility address?", ["A new reader consuming older events", "An old reader consuming every new event", "Business meaning of an absent field"], 0, "Backward describes the new reader's ability to read older data."),
    ("Why lower DNS TTL ahead of a cutover?", ["Old answers may remain cached under their earlier TTL", "The new record immediately clears every resolver", "TLS certificates inherit the DNS TTL"], 0, "Previously cached values keep their old expiry."),
    ("What risk remains when deployment jobs share a concurrency group?", ["A cancelled or replaced run can leave a partial or skipped change", "The group makes database writes atomic", "Required checks apply to every later commit"], 0, "Serialization does not guarantee atomic deployment or check freshness."),
    ("What does an external HTTP probe fail to prove?", ["A business write completed correctly", "The route returned a status code", "The probe reached a TLS endpoint"], 0, "A separate synthetic transaction must verify the business effect."),
    ("What should follow a successful mesh allow test?", ["Test an unauthorized identity and a plaintext route", "Assume all other traffic is denied", "Delete the old service account immediately"], 0, "Negative tests establish the intended boundary."),
    ("What can happen if pool size is raised during slow database locks?", ["More contention and waiting can reach the database", "Locks disappear automatically", "Request deadlines become irrelevant"], 0, "More sessions can amplify the actual bottleneck."),
    ("What should a DNS rollback keep available?", ["Both targets through their respective cache windows", "Only the newly published target", "Neither target once the zone is edited"], 0, "Resolvers may hold either answer until expiry."),
    ("What proves the rollout served the intended revision?", ["A running digest and successful user-path transaction", "A green job from an older commit", "A desired replica count"], 0, "Read-back and user evidence close the release loop."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on mesh identity, node and pool capacity, event history, DNS, and release evidence.",
            sort_order=18500, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(answer - index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, answer, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the operational result that the available evidence supports. Each answer tests a boundary that a single green controller signal cannot establish.</p><h2>Review these lessons</h2>" + links(project_related) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-stateful-operations", "quizzes/devops-operations", "quizzes/devops-advanced-delivery"]) + "<h3>Common Mistakes</h3><ul><li>Do not treat a cached DNS answer as a failed zone edit without checking delegation.</li><li>Do not infer a successful business write from an HTTP health response.</li></ul>"
rows.append(quiz)
quiz_index = by_path[quiz_hub]
quiz_index["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_index["body"] += "<h2>System boundaries check</h2>" + links([quiz_path])
quiz_index["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": target, "title": titles[target]} for target in [project_path, quiz_path])

for source, targets in {
    "devops/network-policy-isolation": ["devops/mesh-identity-boundaries"],
    "devops/capacity-load-testing": ["devops/database-pool-pressure"],
    "devops/kubernetes-resource-budgets": ["devops/node-pressure-eviction"],
    "devops/horizontal-autoscaling": ["devops/node-autoscaling-headroom"],
    "devops/api-compatibility-window": ["devops/event-schema-evolution"],
    "devops/dns-tls-edge": ["devops/dns-cutover-safety"],
    "devops/continuous-integration": ["devops/ci-deployment-concurrency"],
    "devops/observability-signals": ["devops/synthetic-transaction-monitoring"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1,
                  "new_quiz_banks": 1, "total_records": len(rows)}))

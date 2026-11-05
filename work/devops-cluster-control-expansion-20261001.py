"""Add Kubernetes control-plane failure and recovery lessons to the DevOps preview."""

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


def lesson(slug, title, summary, definition, operation, language, sample, cost, mistakes, related):
    path = "devops/" + slug
    assert path not in by_path, path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      operation=operation, language=language, sample=sample,
                      cost=cost, mistakes=mistakes, related=related))


lesson(
    "admission-webhook-outage", "Admission webhook outage: choose a deliberate failure path",
    "Test webhook timeout and failure policy before a cluster upgrade needs new Pods.",
    "A validating or mutating admission webhook sits on the API write path for the requests it matches. An unavailable webhook can stop those writes when its failure policy rejects call errors, or let them proceed without that webhook's decision when the policy ignores call errors. A policy that ignores transport failure still applies a webhook's explicit rejection when the webhook responds. Scope, timeout, and availability matter as much as the policy setting.",
    "A deployment is blocked because its policy webhook Service has no healthy endpoint. Inspect the matching webhook configuration, endpoint availability, certificate expiry, and API rejection messages with the read-only commands. Identify exactly which operations and namespaces the webhook matches; do not disable every policy in the cluster to fix one workload. For a security-critical control, arrange redundant webhook replicas and a recovery path that can restore them without needing the broken webhook itself. For a low-risk mutation, a tested fail-open choice may preserve availability, but record which requests skipped evaluation and reconcile them afterward. In a disposable cluster, stop the webhook, submit a harmless test Deployment, and verify the configured result and timeout. Restore the webhook, then replay validation against objects admitted during the gap. An API write succeeding under fail-open is not proof that the intended policy was enforced.",
    "bash", "kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations\nkubectl get endpointslices -A -l kubernetes.io/service-name=policy-webhook\nkubectl get events -A --sort-by=.lastTimestamp",
    "Long webhook timeouts add latency to every matching API write and can magnify an outage during a rollout. Short timeouts may reject work during a transient pause. A fail-open choice trades enforcement for availability; a fail-closed choice can block recovery if the webhook itself cannot be recreated. Measure admission call latency, call errors, skipped decisions, and rejected requests separately. Keep an approved emergency path narrow and time-bounded.",
    ["Do not treat a successful fail-open write as an enforced policy decision.", "Do not set a broad webhook match without testing its own recovery path.", "Do not confuse an explicit webhook denial with a transport failure policy."],
    ["devops/admission-policy-guardrails", "devops/cluster-upgrade-drill", "devops/gitops-emergency-change", "devops/policy-exception-expiry"],
)

lesson(
    "etcd-quorum-maintenance", "etcd quorum: preserve a voting majority during maintenance",
    "Distinguish a slow API server from a state store that cannot commit writes.",
    "A replicated etcd cluster needs a voting majority to commit changes. In a three-member cluster, one unavailable member can be tolerated; taking a second offline loses write availability. A leader election can briefly pause writes even when a majority survives. Existing application Pods may keep serving traffic while Kubernetes cannot persist a new desired state, making a healthy data plane misleading during control-plane failure.",
    "Before planned maintenance on a self-managed cluster, inventory voting members, their zones, current leader, endpoint health, and a restorable snapshot. The sample uses an already configured, authenticated etcdctl client; it reads status and does not alter membership. Drain or replace only one member at a time, wait for the replacement to catch up, and verify API write health before continuing. If a majority is lost, stop automation that keeps issuing writes. Recover the missing members when possible; if permanent loss forces snapshot recovery, isolate the old cluster so it cannot later rejoin as a competing state source. Reconcile the snapshot's recovery point with external systems before resuming controllers. Managed-cluster users may not have direct etcd access; use the provider's control-plane health evidence and escalation path instead. A snapshot file existing is insufficient: practice restore into an isolated environment and inspect representative cluster objects.",
    "bash", "etcdctl --endpoints=\"$ETCD_ENDPOINTS\" endpoint status --cluster --write-out=table\netcdctl --endpoints=\"$ETCD_ENDPOINTS\" endpoint health --cluster",
    "Extra members increase infrastructure cost, and adding a member to a degraded cluster can change the quorum requirement before it is healthy. Cross-zone placement lowers correlated failure risk but increases network dependence and write latency. Repeated full snapshots consume storage and I/O. Monitor leader changes, failed proposals, disk commit latency, and Kubernetes API write results together. Do not infer quorum from process liveness or a single reachable endpoint.",
    ["Do not restart two of three voting members in one maintenance wave.", "Do not add a member to a broken cluster without calculating the new quorum requirement.", "Do not reconnect an old cluster after snapshot recovery without explicit isolation and reconciliation."],
    ["devops/backup-and-recovery", "devops/cluster-upgrade-drill", "devops/observability-signals", "devops/multi-region-failover"],
)

lesson(
    "pod-address-capacity", "Pod address capacity: diagnose network allocation before adding nodes",
    "Separate CPU headroom from the IP addresses a CNI can assign.",
    "A Pod can remain unable to start when a node has free CPU and memory but its network plugin cannot assign a Pod address. The limit may be a subnet address pool, per-node interface or address capacity, prefix availability, or a plugin-specific allocation rule. In a VPC-addressed cluster, more nodes can consume more subnet addresses and may worsen the shortage.",
    "A claims rollout stalls with network setup events while the autoscaler adds nodes. Inspect the affected Pod events, CNI DaemonSet health, node Pod capacity, and subnet available addresses. The sample includes a provider read-only subnet inventory; use the corresponding control for another CNI. Compare the rollout's peak old-plus-new Pods with available addresses in every target zone, not just the region total. Where prefix allocation is enabled, confirm the required contiguous block can be allocated; a scattered count of free addresses may be insufficient. Free leaked allocations only after their owner is identified. A new subnet or secondary address range requires route, network-policy, and firewall review before use. Test one new Pod on each intended zone, then verify service routing and external egress. Keep a forecast of Pod addresses per surge, autoscaling peak, and warm-pool behavior so the next deployment has a capacity gate.",
    "bash", "kubectl describe pod -n claims claims-api-pending\nkubectl get nodes -o wide\naws ec2 describe-subnets --query 'Subnets[].{Subnet:SubnetId,Zone:AvailabilityZone,Available:AvailableIpAddressCount}' --output table",
    "Larger address pools and extra subnets create routing and security administration work. Warm address reservations improve Pod startup time but reduce addresses available to other workloads. Raising a node's Pod limit without confirming interface and CNI capacity can lead to more scheduled Pods stuck at network setup. Track assignment failures, per-zone free addresses, and successful ready Pods. A scheduler placement success is not the same as a usable networked Pod.",
    ["Do not treat spare node CPU as proof of Pod IP capacity.", "Do not keep scaling nodes into a depleted subnet.", "Do not assume aggregate free addresses form an allocatable prefix."],
    ["devops/node-autoscaling-headroom", "devops/topology-spread-placement", "devops/provider-quota-preflight", "devops/egress-dns-contract"],
)

lesson(
    "csi-volume-attach-ceiling", "CSI attach limits: verify storage placement as well as CPU placement",
    "Read per-node volume limits when stateful Pods stall after scheduling.",
    "A storage driver can advertise how many volumes a node may attach. A Pod can be scheduled but wait for a volume attach, or remain pending when the scheduler knows the node has reached its limit. The effective ceiling depends on the driver, node type, and cloud provider. It is separate from free disk bytes, PersistentVolume size, and CPU capacity.",
    "A settlement StatefulSet adds replicas and several Pods wait for their claims. Inspect Pod events, VolumeAttachment objects, CSINode drivers, the selected node, and volume topology using read-only commands. Determine whether the failure is an attach ceiling, a zone mismatch, a missing driver, or a backend capacity error before moving anything. Calculate volumes already attached plus rollout overlap and sidecar volumes for each eligible node. For a tested recovery, place a replica on a node with attach headroom in the correct zone or add suitable nodes; do not detach an active ledger volume merely to make room. Verify the new Pod mounts the intended claim, opens the data safely, and joins the application without two writers. For a driver that reports stale capacity, follow its supported refresh procedure and confirm actual attached count. A green PersistentVolumeClaim status alone does not prove the Pod can attach it.",
    "bash", "kubectl describe pod -n settlement settlement-db-4\nkubectl get volumeattachments.storage.k8s.io -o wide\nkubectl get csinodes -o yaml",
    "Extra nodes or larger node types cost money; spreading stateful replicas can also increase inter-zone traffic. Repeated attach retries consume control-plane and storage API capacity. A forced detach can corrupt a still-running writer, so recovery must establish ownership and fencing first. Track scheduling failures, attach duration, driver errors, and application readiness by zone. Size surge and failover capacity for attachment slots, not only storage gigabytes.",
    ["Do not equate a Bound claim with a mounted, usable volume.", "Do not force-detach storage from an unverified active writer.", "Do not size node headroom only by CPU and memory for stateful workloads."],
    ["devops/persistent-storage", "devops/statefulset-rollout-safety", "devops/failover-write-fencing", "devops/provider-quota-preflight"],
)

lesson(
    "crd-storage-version-migration", "CRD storage migration: retire an API version only after stored objects move",
    "Track served clients, conversion behavior, and storedVersions separately.",
    "A CustomResourceDefinition can serve more than one API version while storing objects in one chosen version at a time. Changing the storage version does not rewrite old objects automatically. A read served as the new version may be converted on demand while the underlying object remains in the old stored version. Removing the old version too early can break reads, watches, or controller upgrades.",
    "A billing operator moves its InvoiceRun resource from v1beta1 to v1. Keep both versions served while clients change. Test conversion in both directions with real old objects, unknown fields, defaults, and status updates; conversion must preserve the business meaning of each object. Deploy and observe a highly available conversion webhook before setting v1 as storage. Migrate stored objects with a supported migration process, record progress and failures, and verify the CRD's storedVersions no longer lists v1beta1 before dropping it from the specification. The read-only sample reports the served and stored declarations; it does not migrate data. Exercise a watch and a rollback client against a copy of the data. If the conversion webhook is unavailable, even reads of old stored objects requested in the new version can fail. Keep the old path until the rollback window and every cluster's migration evidence are complete.",
    "bash", "kubectl get crd invoiceruns.billing.aitrove.test -o jsonpath='{.spec.versions[*].name}{\"\\n\"}{.status.storedVersions}{\"\\n\"}'\nkubectl get invoiceruns.billing.aitrove.test -A --request-timeout=10s",
    "Serving two versions and running conversion adds API latency, webhook capacity, and upgrade coordination. A bulk rewrite adds etcd writes and can contend with controllers, so throttle it and checkpoint progress. Removing an old version reduces maintenance only after stored objects and clients have moved. Do not patch storedVersions just to make a rollout pass; that status must reflect completed storage migration.",
    ["Do not infer stored data was rewritten because a new-version GET succeeds.", "Do not remove old conversion support while storedVersions still contains the old version.", "Do not treat an untested webhook as a safe rollback path."],
    ["devops/gitops-crd-rollout-order", "devops/api-compatibility-window", "devops/admission-webhook-outage", "devops/database-backfill-checkpoints"],
)

lesson(
    "controller-watch-relist", "Controller watches: recover from expired resource versions without a relist storm",
    "Treat watch continuity as a cache contract rather than an infinite stream.",
    "A Kubernetes watch can end, and an old resourceVersion may no longer be available. A controller that insists on continuing from that version can miss changes or loop on a Gone response. A safe controller rebuilds its local view from a list, resumes watching from the returned version, and reconciles desired effects idempotently. Large, simultaneous relists can strain the API server and its backing store.",
    "A custom receipt controller disconnects during an API-server restart. Keep its last observed resourceVersion with diagnostic context, then treat a version-expired response as a signal to discard the stale cache and relist the relevant resource scope. Use paginated reads where supported, respect API retry guidance, and add jitter so many replicas do not relist at the same instant. The policy fragment describes the loop; it is not a complete client library. After the list, reconcile every observed object and watch from the list's returned version. If a delete happened during the outage, compare the rebuilt set with the prior cache and run finalization only under the controller's idempotency guard. Test repeated disconnects and a restart while a resource changes. Watch count, relist duration, API rejection rate, and reconciliation lag reveal whether recovery is healthy. A connected watch alone does not prove the cache is complete.",
    "text", "Receipt controller watch contract\nLIST scoped resources; retain returned resourceVersion\nWATCH from that version; reconcile each event idempotently\nOn expired version: discard stale cache, jitter, relist, compare sets\nOn API throttle: honor retry guidance and total deadline\nAcceptance: current object set and durable effects match desired state",
    "A relist consumes API and memory capacity proportional to the scoped object set. Narrow selectors help only when they still cover every object the controller owns. Unbounded watch retries can starve the API server during recovery; a fixed synchronized delay can create another burst. Reconciliation must tolerate events repeated after relist. Measure progress from last completed reconciliation, not simply the age of the network connection.",
    ["Do not retry an expired resourceVersion forever.", "Do not accept a newly connected watch as proof the cache is complete.", "Do not let every controller replica relist simultaneously without a rate budget."],
    ["devops/gitops-reconciliation", "devops/cloud-control-plane-throttling", "devops/stuck-finalizer-recovery", "devops/observability-signals"],
)

lesson(
    "priority-preemption-budget", "Pod priority: reserve recovery capacity without evicting the wrong work",
    "Test preemption against application disruption and tenant quotas.",
    "A higher-priority Pod that cannot schedule may cause lower-priority Pods to be terminated so it can fit. Priority affects scheduling decisions and node-pressure eviction, but it does not create CPU, addresses, or attached-volume slots. A disruption budget influences some scheduler choices but should not be treated as an absolute shield against every form of disruption. A badly scoped high-priority class can displace important work across a shared cluster.",
    "A payment gateway needs capacity during node failure while a batch document renderer can pause. Define a limited priority class for the gateway and restrict which teams may use it. The sample is a reviewable class manifest for a disposable cluster; admission and quota controls must separately prevent arbitrary use. Simulate a full node pool and create one replacement gateway Pod. Record which lower-priority Pods are selected, whether their shutdown preserves work, and whether the gateway becomes ready within its objective. Then repeat when a Pod requires an unavailable address or volume slot: preemption should not be presented as a cure for that different limit. Leave a documented batch replay path and alert on sustained Pending gateway Pods, preempted batch work, and unavailable payment replicas. A high priority for every workload collapses the ordering and makes the class useless.",
    "yaml", "apiVersion: scheduling.k8s.io/v1\nkind: PriorityClass\nmetadata:\n  name: payment-recovery\nvalue: 700000\nglobalDefault: false\npreemptionPolicy: PreemptLowerPriority\ndescription: Reserved for payment gateway recovery Pods",
    "Reserved capacity costs money; relying only on preemption saves idle capacity but creates interruption and replay cost for lower-priority work. A grace period for victims can delay the replacement even after they are selected. High-priority usage needs a tenant quota and periodic audit. Track the replacement Pod's actual ready time and the business effect on displaced workloads, not only a scheduler event.",
    ["Do not assign the highest available priority to every production Pod.", "Do not assume a disruption budget prevents every preemption or eviction.", "Do not use priority as a substitute for IP, volume, or zone capacity."],
    ["devops/pod-disruption-budgets", "devops/namespace-resource-quotas", "devops/node-autoscaling-headroom", "devops/queue-consumer-reliability"],
)

lesson(
    "lease-leadership-fencing", "Leader leases: fence side effects after ownership changes",
    "Keep an old leader from committing work after its lease expires.",
    "A Lease object records a leader candidate's ownership and renewal time. It helps controllers coordinate active work, but a paused process can resume after its lease has expired and another candidate has taken over. The old process may still have network access to an external database or provider. The lease alone cannot make that external side effect safe; the effect path needs an epoch or another ownership check the old leader cannot pass.",
    "Two reconciliation workers manage one regional payment route. Inspect the Lease holder and renewal state with the read-only command, then pause the active worker in a disposable test long enough for a standby to take leadership. On resumption, the old worker must recheck its ownership before scheduling more work and must not commit an already prepared route change under an obsolete epoch. A durable route record can require a monotonically increasing generation on every write; the downstream store rejects a lower generation even if the old process is alive. Record lease transitions, accepted and rejected generations, and the actual provider route state. Test a second interruption after the external call succeeds but before the controller records success, using the same operation key to reconcile rather than issuing a new conflicting change. A single current Lease holder is necessary evidence for coordination but insufficient evidence that no stale worker committed an effect.",
    "bash", "kubectl get lease -n payment-system payment-route-leader -o yaml\nkubectl get pods -n payment-system -l app=payment-route-controller -o wide",
    "A shorter lease speeds failover but increases sensitivity to API latency and clock or scheduling pauses. A longer lease slows recovery after a real failure. A durable fencing write adds storage cost and latency, yet prevents a stale owner from corrupting external state. Test the lease duration against observed control-plane delays and stop work when renewal cannot be confirmed. Audit the effect destination, not only the Lease object's holder field.",
    ["Do not infer a prior leader stopped executing because its Lease expired.", "Do not reuse an old epoch after leadership changes.", "Do not retry an ambiguous external mutation under a new operation key."],
    ["devops/partition-rebalance-safety", "devops/failover-write-fencing", "devops/ambiguous-cloud-create-reconcile", "devops/clock-skew-operational-check"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/cluster-control-recovery-project"
quiz_path = "quizzes/devops-cluster-control-failures"
titles[project_path] = "Project: recover a degraded cluster control plane"
titles[quiz_path] = "DevOps cluster control failure decisions"
for item in specs:
    assert all(path in titles for path in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


for heading, summary, slugs in [
    ("API write and state-store availability", "Test admission failure, quorum, and version migration as control-plane dependencies.", ["admission-webhook-outage", "etcd-quorum-maintenance", "crd-storage-version-migration"]),
    ("Scheduling limits beyond compute", "Account for Pod addresses, volume slots, and the cost of preemption.", ["pod-address-capacity", "csi-volume-attach-ceiling", "priority-preemption-budget"]),
    ("Controller continuity", "Rebuild watches safely and fence effects after leader changes.", ["controller-watch-relist", "lease-leadership-fencing"]),
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
               category="DevOps", difficulty="Advanced", tags=["devops", "operations"],
               sort_order=19400 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
                   f"<p>{html.escape(item['operation'])}</p>"
                   f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
                   f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
                   + "<h3>Common Mistakes</h3><ul>"
                   + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
                   + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]]))
    rows.append(row)

project_related = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Exercise admission failure, scheduling ceilings, controller recovery, and fenced leader handoff.",
               difficulty="Advanced", sort_order=19490,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Build the drill in an isolated cluster with synthetic receipt resources, two controller replicas, and a disposable storage driver. Capture API write latency, webhook call errors, Pod network assignment events, volume attach duration, watch relist count, lease holder, and completed receipt effects before changing any failure condition. Keep the state-store portion in a separate self-managed test environment; a managed service may not expose its quorum members.</p>"
    "<h2>Block writes and placement</h2><p>Stop a test admission webhook and submit one safe workload through its exact match rule. Show whether the request is denied, times out, or enters without validation, then restore the webhook and audit the gap. Stop the current etcd leader in the isolated three-voter test and verify writes resume after election; never intentionally stop a second member from a shared cluster. Exhaust a disposable Pod address pool and a CSI attachment slot separately. Record the distinct Pod events and restore each resource before proceeding. Under node pressure, admit one high-priority payment Pod and prove that displaced batch work has a replay path.</p>"
    "<pre><code class=\"language-text\">Cluster control recovery gates\nAdmission: configured failure result and skipped-policy audit\nState store: majority retained; API write verified after election\nNetworking: new Pod gets a usable address and serves a request\nStorage: intended claim mounts without a second writer\nCRD: old stored version removed only after migration\nWatch: cache rebuilt after expired version\nLease: stale leader cannot commit a lower epoch</code></pre>"
    "<h2>Restore controller continuity</h2><p>Serve two versions of a synthetic InvoiceRun custom resource. Write one old-version object, switch the storage version, and show that a new-version read alone does not rewrite the stored object. Run a supported migration and verify storedVersions before removing the old served version. Disconnect the receipt controller until its resourceVersion expires; it must relist, compare the rebuilt object set, and converge without duplicate effects. Pause its leader so the standby acquires the Lease, then resume the old process. The effect store must reject its obsolete generation. Inject a lost provider response after a route write and confirm the current leader reconciles the same operation key.</p>"
    "<h2>Cost and verification</h2><p>Record control-plane requests, extra compute, storage-driver calls, and recovery time. The acceptance record must include a successful synthetic customer request, one durable receipt effect per business key, no active old writer, and a current controller cache. Green Pod status, a Lease holder, or a new-version GET alone does not satisfy those checks. Clean up only the isolated test resources after retaining the evidence.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not disable every admission rule to repair one webhook.</li><li>Do not force-detach a volume from an uncertain writer.</li><li>Do not assume a Lease change fences an external effect.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub]))
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Cluster control recovery drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What does a fail-open admission call error establish?", ["The matching request may proceed without that webhook decision", "The policy was fully evaluated", "Every webhook in the cluster was disabled"], "Availability can be preserved while that webhook's enforcement is skipped."),
    ("Does an explicit webhook denial follow the webhook call failure policy?", ["No; an explicit denial remains a denial", "Yes; it always becomes an allowed request", "Only if etcd has no leader"], "Failure policy addresses call errors, not a received rejection."),
    ("How many unavailable members can a three-voter etcd cluster normally tolerate for writes?", ["One", "Two", "Three"], "A majority of two voters must remain."),
    ("Why might adding nodes worsen a Pod network shortage?", ["New nodes can consume addresses from the same depleted subnet", "Nodes remove every CNI limit", "New nodes turn failed API calls into DNS records"], "Node count and Pod address capacity are separate budgets."),
    ("What does a Bound PersistentVolumeClaim fail to prove?", ["The intended node can attach and mount the volume", "The claim exists", "A storage class was selected"], "Attachment and mount have their own placement and ownership checks."),
    ("What must be checked before dropping an old CRD storage version?", ["Stored objects migrated and storedVersions no longer lists it", "Only a new-version GET succeeds", "Only a new container image was built"], "Read conversion does not rewrite old stored objects."),
    ("What should a controller do after an expired watch resourceVersion?", ["Relist, rebuild cache, then watch from the returned version", "Retry the same expired version forever", "Ignore all prior objects"], "The old watch position cannot be resumed reliably."),
    ("Why should relists include jitter and a request budget?", ["Many controllers can otherwise overload the API server together", "Jitter creates more stored versions", "It prevents all Pod preemption"], "Recovery traffic itself needs admission control."),
    ("What can a high-priority Pod cause under insufficient node capacity?", ["Termination of lower-priority Pods", "Creation of new CPU cores", "Automatic expansion of every subnet"], "Preemption reallocates existing capacity."),
    ("What does Pod priority fail to create?", ["An unavailable Pod address or volume slot", "A scheduling order", "A preemption candidate"], "Priority cannot fix a different hard resource limit."),
    ("Why is a Lease holder insufficient to protect an external write?", ["A stale former leader may resume and reach the external system", "Lease objects cannot have names", "The API server never stores Lease changes"], "The effect path needs a fencing check."),
    ("What proves the control-plane recovery drill completed?", ["A customer path works and old leaders cannot duplicate effects", "Only the controller Pod is Running", "Only the CRD serves a new version"], "Recovery needs the user result and durable ownership evidence."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on webhooks, quorum, scheduling limits, migration, watches, and leases.",
            sort_order=19500, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the operational conclusion supported by actual control-plane and application state. A successful API call, scheduled Pod, or elected leader covers only one boundary.</p><h2>Review these lessons</h2>" + links(project_related) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-cloud-boundary-decisions", "quizzes/devops-host-protocol-failures"]) + "<h3>Common Mistakes</h3><ul><li>Do not treat Pod scheduling as a mounted volume.</li><li>Do not treat a newly served CRD version as completed storage migration.</li></ul>"
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Cluster control check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/admission-policy-guardrails": ["devops/admission-webhook-outage"],
    "devops/cluster-upgrade-drill": ["devops/etcd-quorum-maintenance"],
    "devops/node-autoscaling-headroom": ["devops/pod-address-capacity"],
    "devops/persistent-storage": ["devops/csi-volume-attach-ceiling"],
    "devops/gitops-crd-rollout-order": ["devops/crd-storage-version-migration"],
    "devops/gitops-reconciliation": ["devops/controller-watch-relist"],
    "devops/pod-disruption-budgets": ["devops/priority-preemption-budget"],
    "devops/failover-write-fencing": ["devops/lease-leadership-fencing"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))

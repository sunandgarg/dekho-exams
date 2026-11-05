"""Add cost-and-capacity operating contracts to the local DevOps preview."""

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
    "shared-node-cost-allocation",
    "Shared cluster cost: reconcile service allocation with the provider bill",
    "Separate occupied capacity, platform overhead, and deliberate recovery headroom.",
    "A Kubernetes namespace label is not a cloud invoice line. Node cost covers allocatable capacity, operating-system and kubelet overhead, DaemonSets, spare capacity, and sometimes a second node held for fault tolerance. Allocating the entire bill only to currently busy Pods makes idle capacity disappear from reports even though it remains payable. A useful model reconciles allocated service cost plus explicit shared and unallocated pools to the same billed total for the same period.",
    "A receipt cluster runs three services across a mixed node pool. Export provider usage for a fixed UTC day, join node identity and active time to Pod placement intervals, and attribute a reviewed share using requested CPU and memory over time. Keep node-only charges, storage, network, and control-plane fees in separate buckets until a defensible owner exists. The accounting contract below records the denominator and prevents a dashboard from silently moving spare capacity onto a busy service. Compare the resulting total with the provider bill, including credits and commitment treatment, before calling it complete. Assign an owner to the unallocated pool and investigate missing or unactivated billing tags instead of spreading that gap evenly over application teams. Label changes made after a resource is created may not repair earlier billing records. Keep placement and billing snapshots long enough to explain a previous incident or charge spike, but do not put customer identifiers into cost labels.",
    "text",
    "Receipt cluster daily cost reconciliation\nBilled node total: 100% of matched provider usage\nService allocation: time-weighted requested CPU and memory shares\nPlatform allocation: system Pods and managed control-plane charges\nRecovery reserve: explicitly owned spare-node capacity\nUnallocated: missing identity or unmatched billing record\nCheck: service + platform + reserve + unallocated = billed total",
    "Calculating time-weighted allocation over P Pod placement intervals and B billing records needs at least a pass over both datasets; aggregating by service also needs storage proportional to the number of service keys. Overly detailed labels can make joins and reports expensive without improving decisions. Measure the unallocated percentage, idle-node hours, cost per successful receipt, and how the figures move during a release or incident. Do not cut a reserve node merely because the allocation report calls it idle.",
    ["Do not equate Pod CPU use with the complete billed node cost.",
     "Do not hide unallocated charges by distributing them without an owner.",
     "Do not present a discounted or credited rate as a capacity guarantee."],
    ["devops/cost-capacity-ownership", "devops/kubernetes-resource-budgets", "devops/node-autoscaling-headroom", "devops/release-evidence-record"],
)

lesson(
    "request-rightsize-hpa-coupling",
    "CPU request rightsizing: account for the HPA feedback loop",
    "Changing a request changes both scheduling and utilization-based scaling.",
    "Kubernetes schedules a Pod against its resource request. An HPA CPU utilization target compares measured CPU use with requested CPU, so a request change can alter desired replicas even when traffic and actual CPU are unchanged. Shrinking requests to fit more Pods may increase the reported utilization and trigger more replicas; raising requests can delay scaling while reserving more node capacity. A cost comparison that ignores this control loop is incomplete.",
    "A parcel-rating API uses a CPU-utilization HPA and sometimes saturates during carrier batch imports. Record per-Pod CPU, p95 latency, throttle time, replica count, node count, and pending Pods over a normal week and a known peak. Apply a small request change to one canary Deployment, leaving the HPA target and load shape explicit. The fragment represents the container request and limit; use it inside the reviewed workload manifest. Compare the same workload before and after the change, including new-node startup and rollback surge. If sidecars use CPU, check whether the HPA uses Pod-level or container-level utilization so the denominator matches the intended work. Do not combine request reduction with a simultaneous algorithm change; that destroys attribution. Verify memory separately, because an inexpensive CPU request cannot prevent an OOM kill. Roll back if latency or error budget deteriorates even when billed node-hours fall.",
    "yaml",
    "resources:\n  requests:\n    cpu: 340m\n    memory: 620Mi\n  limits:\n    memory: 1Gi",
    "The apparent saving from lower requested CPU may vanish when the HPA creates more replicas or when node fragmentation leaves the same number of nodes running. Conversely, a larger request can reduce replica churn but strand capacity. Measure cost per successful rating at a fixed demand level, ready replicas at peak, scheduler Pending time, and p95 latency. The sample values are a canary hypothesis, not a sizing recommendation; derive production requests from observed load and failure headroom.",
    ["Do not adjust CPU requests without checking the HPA's utilization denominator.",
     "Do not infer a smaller bill from fewer requested cores alone.",
     "Do not use average CPU as the only sizing input when tail latency and cold starts matter."],
    ["devops/kubernetes-resource-budgets", "devops/horizontal-autoscaling", "devops/hpa-stabilization-boundaries", "devops/shared-node-cost-allocation"],
)

lesson(
    "interruptible-worker-checkpoint-budget",
    "Interruptible compute: price recovery work, not only cheap node hours",
    "A batch worker is eligible only when it can lose a node without losing its job.",
    "Interruptible capacity can be withdrawn by its provider, and any warning window is provider-specific and may be too short for a large checkpoint. A PodDisruptionBudget governs voluntary evictions through the Eviction API; it does not block an involuntary node loss. A discounted node hour has little value if interruption causes duplicate side effects, a long replay, or an SLO breach.",
    "A document-index worker consumes queued archive chunks. Put only replayable workers on an interruptible pool, keep the authoritative job state and checkpoint outside the node, and acknowledge a queue lease only after a durable checkpoint. Bound one work unit so it can finish or safely resume within the available lease and interruption budget. Inject a node loss with no warning in a disposable environment, then verify that another worker resumes at the last committed offset, does not publish a duplicate index generation, and eventually releases the old claim. The checklist below separates provider notice from application correctness. Vary node type and zone eligibility so the pool can obtain replacement capacity; a design that requires one scarce shape may be unavailable precisely when interrupted. Keep a non-interruptible fallback for critical deadlines and define when it is activated, rather than assuming the discounted pool can always replace itself.",
    "text",
    "Document-index interruption acceptance\nAuthoritative state: durable checkpoint and idempotent generation key\nNo-notice test: worker killed during publish and replayed once\nLease rule: acknowledgement follows durable checkpoint\nReplacement: compatible capacity available outside one node shape\nDeadline: fallback pool starts before queue age violates the service objective\nCost: node saving minus replay, fallback, and transfer cost",
    "The relevant unit is cost per completed indexed archive, including retried CPU, queue retention, fallback nodes, and data transfer. Measure interruption frequency, lost work per event, replay duration, duplicate-publish attempts, and queue age. A short checkpoint interval raises storage writes; a long interval raises replay cost. Find the interval from observed work-unit cost and recovery objective rather than copying a provider notice duration into the application design.",
    ["Do not treat a PDB as protection from provider interruption.",
     "Do not move a non-idempotent publisher onto interruptible nodes without a replay contract.",
     "Do not count a discount without charging replay and fallback capacity to the same workload."],
    ["devops/queue-visibility-lease", "devops/partition-rebalance-safety", "devops/pod-disruption-budgets", "devops/node-autoscaling-headroom"],
)

lesson(
    "compute-commitment-capacity-separation",
    "Compute commitments: separate billing coverage from machine availability",
    "A discounted commitment and a capacity reservation solve different problems.",
    "A compute spending commitment may discount eligible usage over a term without reserving a particular machine at the moment a service needs it. A capacity reservation, where a provider offers one, addresses supply in a specified scope and has its own charges and constraints. Treating a discount as failover capacity can leave a recovery plan financially tidy and operationally impossible.",
    "A payments API has a stable baseline, a release surge, and a separate regional recovery target. Estimate the baseline from several demand cycles and remove unusual incident and migration peaks before discussing a long-lived commitment. Keep the burst and recovery requirement as independent capacity questions: which shapes, zones, quotas, and reservations can actually be acquired within the recovery objective? The decision record below distinguishes financial coverage from physical availability and forbids using the same spare node as both a production surge buffer and a full regional restore. Evaluate utilization under low-demand months as well as peak periods; an unused commitment can erase its expected discount. Model the effect of an architecture change that shifts usage to another instance family or provider service. Require finance and service owners to approve the obligation, and verify the provider's current terms rather than copying a percentage from a tutorial.",
    "text",
    "Payments compute decision record\nStable eligible baseline: measured usage by hour and service\nCommitment: term, scope, utilization floor, owner\nSupply requirement: node shapes, zones, quota, acquisition time\nRecovery requirement: independent spare or reservation evidence\nScenario checks: quiet month, normal peak, region loss, migration\nApproval gate: service owner and finance review current terms",
    "A commitment can lower unit price while increasing the cost of changing architecture or underusing the purchased amount. A reservation can improve availability while adding idle charges. Measure coverage, utilization, unused obligation, acquisition time, and the probability of missing recovery capacity under each scenario. A spreadsheet that minimizes average monthly cost is not enough; the decision must show the service's worst credible capacity event and the obligations left after a migration.",
    ["Do not call a spending commitment a machine reservation.",
     "Do not commit based only on a peak month.",
     "Do not allocate the same recovery headroom to two simultaneous failures."],
    ["devops/cost-capacity-ownership", "devops/provider-quota-preflight", "devops/multi-region-failover", "devops/shared-node-cost-allocation"],
)

lesson(
    "cross-zone-transfer-cost-path",
    "Cross-zone data paths: measure bytes before changing placement",
    "A topology change can move the bill from compute to network transfer.",
    "A service request may cross node, zone, and region boundaries on its way to storage, a dependency, or a standby. Providers price these paths differently and sometimes charge both transferred bytes and an intermediate network service. A topology rule that improves resilience or scheduling balance can therefore change recurring transfer cost without changing application request count.",
    "A receipt API writes to a zonal database and reads replicated objects. Map source Pod zone, destination zone, bytes by direction, request frequency, and the service or gateway in between. Compare a normal hour, peak hour, backup copy, and failover rehearsal. The read-only commands below collect Pod and node placement; join their output with flow logs, database metrics, and provider billing records because Kubernetes metadata alone does not count transferred bytes. Distinguish an intentional cross-zone replica write from accidental hairpin traffic through a proxy in a different zone. Test a local-route candidate with real latency and failure injection before moving a critical dependency; a cheaper path that loses access after one zone failure may cost more in downtime. For region-level replication, budget both steady-state change traffic and a full reseed after a disaster. Record compression and retry overhead so the estimate reflects wire bytes, not only payload bytes.",
    "bash",
    "kubectl -n checkout get pods -l app=receipt-api -o wide\nkubectl get nodes -L topology.kubernetes.io/zone\nkubectl -n checkout get endpointslices -l kubernetes.io/service-name=receipt-db -o wide",
    "Transfer cost scales with bytes and path-specific rates; retries, dual writes, and failover can multiply it. The analysis requires a pass over flow or usage records for the chosen time window, with aggregation memory proportional to the number of source-destination pairs. Measure bytes per successful receipt, cross-zone share, failover reseed volume, and p95 latency. Do not hard-code a provider rate in the lesson or assume every same-region path is free; verify current billing terms for the deployed region.",
    ["Do not infer transferred bytes from Pod placement alone.",
     "Do not collapse backup reseed traffic into an average steady-state number.",
     "Do not remove cross-zone replication solely to lower transfer charges without a recovery test."],
    ["devops/topology-spread-placement", "devops/multi-region-failover", "devops/dns-cutover-safety", "devops/cost-capacity-ownership"],
)

lesson(
    "nat-endpoint-cost-boundary",
    "NAT and private endpoints: compare the complete route and failure domain",
    "Hourly, processed-byte, and cross-zone charges can stack on one egress path.",
    "A private workload often reaches a managed service through a NAT gateway, a private endpoint, or another controlled network path. These options have different hourly, processed-byte, data-transfer, DNS, and availability properties. An endpoint can remove one metered hop for a supported service, but it can also add its own charges or fail if the workload still resolves and routes to the public destination.",
    "A document processor pulls from object storage and sends telemetry to an external collector. For each destination, draw the actual DNS answer, route table match, zone, gateway or endpoint, and authenticated target. In a disposable network, move the object-storage path to a supported private endpoint while leaving the external collector on its approved egress route. Verify flow logs and a real read from every workload zone; merely creating an endpoint does not prove traffic uses it. Test a gateway or endpoint failure and confirm the service either fails closed or follows an explicitly approved fallback. Compare one gateway per zone with a shared gateway, including cross-zone transfer, fixed hourly charges, processed bytes, and the effect of a zone outage. The route checklist below is intentionally provider-neutral; use the current service-specific rate card for actual estimates. Do not route sensitive traffic around inspection simply because an alternate path is cheaper.",
    "text",
    "Document-processor route review\nDestination: object storage or external telemetry collector\nDNS: answer seen from each workload zone\nRoute: selected gateway or private endpoint\nProof: flow record plus authenticated request\nBill: fixed hours + processed bytes + transfer bytes\nFailure: zone loss and approved fallback behavior\nOwner: network and service teams approve the path",
    "The cheapest path at one traffic volume may not be cheapest at another because fixed and per-byte components differ. Estimate both a quiet month and a peak/reseed month, then account for operational redundancy. Measure gateway bytes, endpoint bytes, cross-zone transfer, failed connections, and DNS-route mismatches. A saving that removes an independent zone path can violate the service's availability target, so compare cost with the tested failure outcome.",
    ["Do not assume creating a private endpoint moves traffic onto it.",
     "Do not count only hourly gateway charges while ignoring processed and transferred bytes.",
     "Do not centralize egress across zones without testing the resulting failure domain."],
    ["devops/nat-port-allocation-pressure", "devops/egress-dns-contract", "devops/cross-zone-transfer-cost-path", "devops/network-path-diagnosis-project"],
)

lesson(
    "budget-signal-delay-guardrail",
    "Cost alerts: account for billing delay before a runaway resource spreads",
    "A provider budget signal is usually slower than a deployment or job loop.",
    "Billing and budget systems aggregate usage after it happens. Their alerts can arrive after a fast autoscaling event, log loop, or accidental data transfer has already incurred charges. A budget is therefore a review and escalation signal, not a synchronous safety control for infrastructure APIs. Real-time operational limits need a separate quota, concurrency cap, TTL, or approval path.",
    "A test pipeline accidentally creates a large fleet of preview environments. Give each environment an owner, creation record, expiry, and resource quota before the first run. Put a maximum concurrent environment count in the controller and a separate provider account limit where appropriate. Watch creation rate and active resource count within minutes, while using billing alerts to reconcile the eventual charge. The policy fragment distinguishes the fast operational gate from delayed financial reporting. Inject a failed cleanup and confirm the controller stops creating new environments while an operator can still recover or delete the leftovers. Avoid automatic deletion of a production resource just because an estimated bill crosses a threshold; false attribution or delayed corrections can make that action destructive. Route a budget anomaly to the team that owns the resource and include the usage dimension and deployment change that preceded it. Test notification delivery instead of assuming a configured alert reaches someone.",
    "text",
    "Preview-environment cost controls\nSynchronous: controller concurrency cap and namespace quota\nLifecycle: owner, creation time, TTL, cleanup state\nNear-real-time: active count, creation rate, transfer bytes\nDelayed: provider budget and anomaly alert with billing timestamp\nResponse: pause new previews, inspect owner and recent changes\nDeletion: reviewed cleanup path with production exclusions",
    "A tighter cap slows parallel tests but limits a runaway provisioning loop. A loose cap improves developer throughput while raising the worst-case bill before delayed alerts arrive. Measure time from resource creation to local limit, billing visibility lag, unowned resources, and alert delivery. Choose the cap from acceptable exposure during that lag, then review it when test demand changes. Do not claim exact current spend from an incomplete billing feed.",
    ["Do not treat a delayed budget alert as an API admission rule.",
     "Do not delete resources automatically from a noisy or unverified cost estimate.",
     "Do not omit notification-delivery tests and ownership mapping."],
    ["devops/ephemeral-environment-controls", "devops/provider-quota-preflight", "devops/cost-capacity-ownership", "devops/alert-design"],
)

lesson(
    "node-consolidation-disruption-budget",
    "Node consolidation: calculate the capacity needed to evict safely",
    "Removing a low-use node still requires room for its Pods and their constraints.",
    "A node with low CPU use is not automatically removable. Its Pods may have large resource requests, a restricted zone, local storage, scarce attach slots, or a PodDisruptionBudget that currently allows no voluntary eviction. A consolidation controller that respects the Eviction API can wait for those constraints, while an involuntary node loss remains possible. Cost savings require a post-move node count, not just an eviction attempt.",
    "A parcel API has one lightly used node beside a stateful ledger and a scheduled batch worker. Before consolidating, list requests, node affinity, topology spread, volume attachments, PDB disruptions allowed, and the surge reserve for the next release. The read-only commands below are a starting inventory; test eviction and replacement in an isolated pool. Move a replayable worker first, verify the queue lease and workload latency, and only then attempt the API Pod. If no destination node has enough allocatable resources, consolidation will fail or trigger a new node, producing no saving. Check how the provider bills partial node-hours and any minimum node-pool size. Keep capacity for a node failure and rollback after consolidation. If a PDB blocks a voluntary eviction, adjust workload availability or schedule maintenance; do not bypass it with direct Pod deletion to obtain a short-lived saving. Record exactly which node-hours were removed and which replacement resources were added.",
    "bash",
    "kubectl -n parcel get pdb -o wide\nkubectl -n parcel get pods -o wide\nkubectl get nodes -L topology.kubernetes.io/zone\nkubectl -n parcel describe pod parcel-api-canary",
    "Consolidation may reduce node-hours but increase scheduling latency, hotspot risk, or recovery time. A drain also creates temporary duplicate capacity while replacements start, so the billing benefit may begin later than the controller's decision. Measure actual nodes removed, replacement starts, disruptions allowed, pending-Pod time, p95 latency, and recovery headroom. Count repeated failed attempts as control-plane and operator cost even when they do not change the bill.",
    ["Do not classify a node as removable from CPU utilization alone.",
     "Do not bypass PDBs or local-volume constraints to force a cheaper topology.",
     "Do not report savings until the billed node count actually falls."],
    ["devops/pod-disruption-budgets", "devops/node-autoscaling-headroom", "devops/csi-volume-attach-ceiling", "devops/shared-node-cost-allocation"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/cost-capacity-recovery-project"
quiz_path = "quizzes/devops-cost-capacity-decisions"
titles[project_path] = "Project: lower platform cost without losing recovery capacity"
titles[quiz_path] = "DevOps cost and capacity decisions"
assert all(path in titles for item in specs for path in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


for heading, summary, slugs in [
    ("Allocation and request feedback", "Reconcile the provider bill and test how request changes affect scheduling and HPA behavior.", ["shared-node-cost-allocation", "request-rightsize-hpa-coupling"]),
    ("Interruptions and commitments", "Price replay work and distinguish discounted usage from guaranteed capacity.", ["interruptible-worker-checkpoint-budget", "compute-commitment-capacity-separation"]),
    ("Network path cost", "Measure cross-zone bytes and compare gateway and private-endpoint routes.", ["cross-zone-transfer-cost-path", "nat-endpoint-cost-boundary"]),
    ("Guardrails and consolidation", "Use fast operational limits and prove a node can be removed without exhausting recovery headroom.", ["budget-signal-delay-guardrail", "node-consolidation-disruption-budget"]),
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
               sort_order=21600 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['operation'])}</p>"
        f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
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
               summary="Reconcile spend, test interruption and network paths, and retain proven recovery capacity.",
               difficulty="Advanced", sort_order=21690,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use a disposable cluster, synthetic billing export, and fault-injection node pool. Define the service's latency objective, queue-age limit, rollback capacity, and recovery deadline before changing any cost control. Reconcile provider records for one quiet and one peak day, including shared node hours and unallocated charges. No estimated saving is accepted until the bill, workload demand, and user-path result agree for the same interval.</p>"
    "<h2>Test compute decisions</h2><p>Calculate time-weighted service allocation while retaining explicit platform and recovery-reserve buckets. Change one API CPU request and watch HPA replicas, Pending time, node count, and p95 latency under a fixed load. Move one idempotent indexing worker to an interruptible pool; kill its node with no warning and verify checkpoint replay, lease release, and one published generation. Model a spending commitment separately from a capacity reservation, then test whether a region-loss recovery demand can actually acquire its node shapes within the deadline. Attempt consolidation of a lightly used node only after checking requests, PDBs, volume constraints, and replacement headroom.</p>"
    "<pre><code class=\"language-text\">Cost and recovery acceptance gates\nAllocation: service + platform + reserve + unallocated equals billed total\nRightsizing: latency and ready replicas remain within objectives\nInterruption: checkpoint resumes without duplicate publication\nCommitment: discount does not stand in for machine availability\nNetwork: billed route and measured byte path agree\nBudget: fast cap stops creation before delayed billing alert\nConsolidation: billed node count falls and one-node recovery remains possible</code></pre>"
    "<h2>Test network and alert paths</h2><p>Map receipt traffic by source zone, destination, gateway, and bytes, including a backup reseed. Route a supported storage service through a private endpoint in a disposable network; verify flow logs, DNS, and authenticated reads from each workload zone. Simulate endpoint or gateway loss and confirm approved fallback behavior. Create previews rapidly until the controller cap stops them, while recording the later provider-budget notification timestamp. Do not delete a production resource from a synthetic cost anomaly. Show an owner for every leftover resource and an explicit cleanup state.</p>"
    "<h2>Cost and verification</h2><p>Report cost per successful transaction and archive, actual node-hours removed, replay CPU, transfer bytes, budget lag, and p95 latency before and after each change. Keep rate inputs as current provider data outside public lesson copy. Mark a scenario unverified when its cloud billing, capacity pool, or failure mode could not be reproduced. A lower estimated bill is not an accepted outcome if the recovery objective is no longer met.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not allocate away deliberate recovery reserve.</li><li>Do not treat a financial discount as guaranteed replacement capacity.</li><li>Do not infer a cheaper route from resource names without measuring bytes and billing.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Cost and capacity recovery drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What must a shared-node allocation reconcile to?", ["The provider bill for the same period", "Only Pod CPU samples", "Only namespace labels"], "Explicit platform, reserve, and unallocated buckets keep the total visible."),
    ("What else changes when a CPU request changes under utilization-based HPA?", ["The utilization denominator", "The provider's list price", "The application's source code"], "HPA compares CPU use with the request."),
    ("What does a PDB protect when an interruptible node is withdrawn?", ["It does not block that involuntary loss", "It guarantees the node remains", "It stores a checkpoint"], "PDBs govern voluntary eviction through the API."),
    ("Which event should precede queue acknowledgement for a replayable worker?", ["Durable checkpoint or completed side effect", "Starting a timer", "Seeing a cheap node"], "The next worker needs authoritative state."),
    ("Does a compute spending commitment guarantee a machine is available?", ["No, capacity must be checked separately", "Yes, in every zone", "Yes, after a Pod restart"], "A financial benefit and supply assurance are distinct."),
    ("Which traffic matters in a cross-zone cost estimate?", ["Measured wire bytes including retries and reseed", "Only request count", "Only database row count"], "The billed path follows transferred bytes and intermediary services."),
    ("What proves a private endpoint is carrying intended traffic?", ["Flow evidence and a real authenticated request from each workload zone", "Only an endpoint object exists", "Only a Pod is Ready"], "DNS and routing can keep traffic on an earlier path."),
    ("What cost parts can stack on a gateway path?", ["Fixed hours, processed bytes, and transfer charges", "Only CPU requests", "Only Pod memory limits"], "One route can incur several billing dimensions."),
    ("Why is a budget alert insufficient as a fast creation cap?", ["Billing data and alerts can lag resource creation", "It prevents every API call", "It replaces quotas"], "A synchronous controller or quota must bound rapid growth."),
    ("What should happen before automated deletion from a cost anomaly?", ["Ownership and cause must be verified through a reviewed path", "Every resource must be deleted", "The alert must be ignored"], "Delayed or misattributed estimates can cause destructive action."),
    ("Why might a low-CPU node resist consolidation?", ["Requests, placement, storage, or PDB constraints", "Its CPU is always free", "It has no invoice"], "Replacement Pods need compatible capacity and allowed eviction."),
    ("When is a consolidation saving real?", ["After billed node count falls without losing recovery headroom", "When an eviction is requested", "When CPU use falls for one minute"], "An attempted move can create a replacement node and no saving."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on billed cost and usable recovery capacity.",
            sort_order=21700, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Decide whether an apparent saving survives billing reconciliation, application demand, interruption, and a one-node failure. Separate a financial rate change from the ability to acquire capacity when it is needed.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-runtime-isolation-decisions", "quizzes/devops-storage-lifecycle-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not call unallocated cost zero.</li><li>Do not make an availability decision from a discounted price alone.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Cost and capacity check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/cost-capacity-ownership": ["devops/shared-node-cost-allocation", "devops/compute-commitment-capacity-separation", "devops/budget-signal-delay-guardrail"],
    "devops/kubernetes-resource-budgets": ["devops/request-rightsize-hpa-coupling"],
    "devops/horizontal-autoscaling": ["devops/request-rightsize-hpa-coupling"],
    "devops/node-autoscaling-headroom": ["devops/interruptible-worker-checkpoint-budget", "devops/node-consolidation-disruption-budget"],
    "devops/pod-disruption-budgets": ["devops/node-consolidation-disruption-budget"],
    "devops/multi-region-failover": ["devops/compute-commitment-capacity-separation", "devops/cross-zone-transfer-cost-path"],
    "devops/nat-port-allocation-pressure": ["devops/nat-endpoint-cost-boundary"],
    "devops/ephemeral-environment-controls": ["devops/budget-signal-delay-guardrail"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))

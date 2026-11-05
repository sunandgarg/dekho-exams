"""Add cloud boundary and overload recovery content to the DevOps curriculum."""

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
    "nat-port-allocation-pressure", "NAT port pressure: find the shared outbound ceiling",
    "Correlate new-connection failures with translation capacity before scaling callers.",
    "A shared NAT gateway translates private outbound connections into a finite set of address and port combinations. Many short connections to the same destination can exhaust available translations even when the application Pods, DNS, and remote API are healthy. The resulting connection errors can appear in several unrelated services at once because their egress path is shared.",
    "A receipt service and an alert worker both start timing out against one payment endpoint after a rollout triples worker count. First group failures by destination address and port, source subnet, and gateway; check gateway port-allocation errors, active connections, and dropped packets over the same minutes. The read-only sample fetches recent gateway metrics in an approved account. Compare the trend with connection creation in clients. Restore bounded connection pooling and keep-alive, limit concurrent dials, and test a small traffic slice before increasing gateway address capacity. If a provider offers private connectivity, evaluate its cost and routing separately. An idle connection may be removed by network infrastructure; a pool must validate or replace it rather than treating any old socket as usable. Confirm successful application transactions after the change, not merely a falling gateway counter.",
    "bash", "aws cloudwatch list-metrics --namespace AWS/NATGateway --metric-name ErrorPortAllocation --dimensions Name=NatGatewayId,Value=nat-0123456789abcdef0\naws cloudwatch list-metrics --namespace AWS/NATGateway --metric-name ActiveConnectionCount --dimensions Name=NatGatewayId,Value=nat-0123456789abcdef0",
    "Connection reuse reduces port churn and handshake cost but holds sockets and application memory. More gateway addresses or separate egress paths add spend and can hide a client-side connection leak. Metric discovery does not return data points; graph the metric with the incident time window before deciding. Keep a per-destination connection budget and a test for idle-socket recovery. Scaling callers without checking the shared NAT path can make the outage wider.",
    ["Do not read a healthy Pod network interface as proof the shared gateway has ports.", "Do not multiply clients while connection creation is exhausting a shared destination path.", "Do not assume an idle pooled socket survives every gateway timeout."],
    ["devops/egress-dns-contract", "devops/file-descriptor-exhaustion", "devops/retry-timeout-budgets", "devops/capacity-load-testing"],
)

lesson(
    "cloud-control-plane-throttling", "Cloud API throttling: keep infrastructure changes inside a request budget",
    "Separate rate limits from hard quotas and bound automation retries.",
    "A cloud control plane can reject bursts even when the requested infrastructure has room to exist. A 429 or provider throttling response is a rate signal; a quota-exceeded response may require a limit increase or design change. Concurrent deploy jobs, inventory scans, and autoscalers can share an account or regional request budget. Blind retries can turn one slow rollout into a control-plane flood.",
    "A regional failover job creates instances while several pipelines refresh infrastructure state. Record the operation, account, region, response code, request ID, and retry count without storing credentials. Cap concurrent mutating calls per operation family. Where supported, honor server retry guidance; otherwise use bounded exponential delay with jitter and a total deadline. The text policy is an operational contract, not a provider API configuration. Read back a timed-out create before resending it, and retain the same idempotency token if the API supports one. Pause nonessential inventory scans while preserving health and rollback operations. Test that one throttled job eventually stops and hands an actionable record to an operator instead of retrying forever. A successful retry proves that request succeeded; it does not prove the whole rollout reached its intended state.",
    "text", "Control-plane request policy\nScope: account + region + operation family\nConcurrent mutations: 4 per scope\nRetry: transient throttle only; jittered delay; 90-second total deadline\nAmbiguous create: read back by stable operation key before retry\nFailure record: request ID, last response, resources found, next safe action",
    "Lower concurrency may slow provisioning but leaves capacity for rollback and incident response. Extra retries consume the same quota they are trying to survive. Rate budgets must include SDK retries, orchestration retries, and human-run tools, or the effective attempt count can multiply. Do not place every independent service behind one adaptive limiter unless that shared behavior is intended. Measure request rate, throttled responses, rollout duration, and desired-versus-actual resources together.",
    ["Do not retry a hard service quota error as though it were transient throttling.", "Do not add an outer retry loop without counting SDK attempts.", "Do not resend an ambiguous create with a fresh operation identity."],
    ["devops/terraform-state-and-plan", "devops/retry-timeout-budgets", "devops/node-autoscaling-headroom", "devops/multi-region-failover"],
)

lesson(
    "provider-quota-preflight", "Provider quota preflight: reserve capacity for rollback and recovery",
    "Check regional and account limits before a release depends on new resources.",
    "A service quota limits a resource count or capacity, while a request-rate limit governs how quickly API calls can be made. An otherwise correct deployment can stall when it needs another public address, volume, load balancer, or compute unit. Recovery capacity must be considered separately from steady state: a canary, replacement, and rollback may coexist for a period.",
    "Before replacing a payment API node group, calculate peak simultaneous demand: existing nodes plus rollout surge plus the reserved recovery slice. Compare that demand with account and regional quota, current use, subnet addresses, and any organization policy that narrows eligibility. The read-only command lists an approved account's EC2 quota catalog; select and verify the exact quota code for the resource in use rather than assuming the catalog entry measures current consumption. Submit a limit change early when required and run a small allocation test in the target zone. Leave room for rollback after the new revision is placed. When capacity is unavailable during an incident, reduce nonessential workloads through a documented priority order instead of deleting healthy recovery assets at random. Record the accepted limit, observed use, and region for the release gate.",
    "bash", "aws service-quotas list-service-quotas --service-code ec2 --query 'Quotas[].{Name:QuotaName,Code:QuotaCode,Value:Value}' --output table\naws ec2 describe-subnets --query 'Subnets[].{Subnet:SubnetId,Available:AvailableIpAddressCount,Zone:AvailabilityZone}' --output table",
    "Holding spare address and compute capacity costs money, but a failed surge can prolong an outage. A quota listing alone cannot prove a resource can be allocated in the chosen zone or subnet. Reconcile actual use from the resource inventory and test the exact placement path. A rollback can need additional capacity even while the failed revision exists, so a plan that only fits steady state is incomplete.",
    ["Do not confuse a rate throttle with an exhausted resource quota.", "Do not size only for the final replica count when old and new revisions overlap.", "Do not treat a quota listing as proof of zone-level availability."],
    ["devops/node-autoscaling-headroom", "devops/capacity-load-testing", "devops/multi-region-failover", "devops/terraform-state-and-plan"],
)

lesson(
    "queue-age-scaling-contract", "Queue-age scaling: target completion time, not only queue length",
    "Tie consumer replicas to arrival rate, processing duration, and downstream limits.",
    "Queue depth shows unfinished work but does not by itself describe how long the oldest item has waited. A worker scaler may include in-flight messages, which changes the meaning of its target. More consumers can shorten backlog only while the database, remote API, and broker can serve the added concurrency. Delayed messages, poison items, and long visibility leases can distort a single depth number.",
    "A billing queue holds 2,400 receipts after a provider outage. Measure visible count, in-flight count, oldest eligible age, arrival rate, completion rate, and per-worker processing time. Set a temporary age objective and calculate the drain rate needed to meet it, then cap worker concurrency at the downstream payment API and database budgets. This policy sample makes the limit explicit; implement the equivalent controls in the actual scaler and worker. Test scale-from-zero by publishing one item, including the time until a worker is ready. Keep a small warm floor when that cold-start delay violates the age objective. During recovery, watch completed receipts and oldest age; a falling visible count caused only by long in-flight leases is not successful drainage. Reduce the worker ceiling if provider throttling or database wait time climbs. Replay dead-lettered work under its own rate budget after normal intake stabilizes.",
    "text", "Billing queue recovery gate\nOldest eligible age objective: under 6 minutes\nObserve: visible, in-flight, delayed, completed/minute, failure/minute\nWorker ceiling: min(queue demand, database slots, provider rate budget)\nScale-from-zero test: one receipt reaches durable completion\nRollback: lower worker ceiling if downstream wait or 429 rate rises",
    "A warm worker floor increases compute cost. Aggressive scaling can spend more while reducing completed throughput if every worker contends for the same dependency. Age is a service outcome; use depth and throughput to explain it. Estimate the drain window from net completion rate after new arrivals, not a single static queue count. Keep the lease and idempotency contract valid as replica count changes.",
    ["Do not count in-flight messages as completed work.", "Do not choose a replica target without measuring processing time and downstream capacity.", "Do not assume scale-from-zero meets an age objective until the cold path is tested."],
    ["devops/queue-consumer-reliability", "devops/queue-visibility-lease", "devops/database-pool-pressure", "devops/hpa-stabilization-boundaries"],
)

lesson(
    "retry-amplification-control", "Retry amplification: assign one owner for each failed operation",
    "Account for attempts made by the client, proxy, SDK, and queue worker.",
    "Retries at multiple layers multiply request volume. If a caller makes three attempts and its proxy makes three attempts per call, a single operation can produce nine backend requests before a queue redelivery is counted. Each layer may look locally reasonable while the shared dependency receives a burst precisely when it has the least spare capacity.",
    "Trace one failed payout through the HTTP client, mesh proxy, provider SDK, and queue worker. Log an operation key, attempt number, and layer at each boundary; avoid logging the payment credential. Make one layer responsible for a bounded transient retry, and set a total deadline from the user's operation, not a fresh deadline for every attempt. Permit a retry only when the method and durable effect are safe under the original idempotency key. Return a final failure or park the work when the deadline expires. During a load test, inject a short provider outage and compare primary request rate, retry request rate, provider error rate, and completed payments. The contract below allows two total provider sends; a queue redelivery resumes the same business key and still checks whether the effect already committed. A retry budget should be reduced during overload rather than increasing attempts because failures are frequent.",
    "text", "Payout attempt contract\nBusiness key: original payout operation ID\nRetry owner: payout worker only\nProvider sends: 2 maximum inside 12-second operation deadline\nProxy and SDK additional retries: disabled for this call\nTransient response: bounded jitter before second send\nAmbiguous result: read durable provider status before another send",
    "A stricter retry limit may surface some transient errors sooner, but it protects recovery capacity and makes failure visible. Every extra attempt consumes network, CPU, provider quota, and sometimes money. Monitor retries as a fraction of original requests and count effects by business key, since a low error rate can hide duplicate writes. A no-retry decision is safe only when an explicit recovery path exists for incomplete work.",
    ["Do not reset the deadline at each network hop.", "Do not count only application attempts when a proxy or SDK retries too.", "Do not retry an ambiguous side effect under a new operation key."],
    ["devops/retry-timeout-budgets", "devops/queue-consumer-reliability", "devops/overload-shedding", "devops/queue-visibility-lease"],
)

lesson(
    "circuit-breaker-recovery-probes", "Circuit breaker recovery: probe capacity without reopening a flood",
    "Use bounded trial requests and distinguish fallback from true dependency health.",
    "A circuit breaker stops sending some calls to a failing dependency after a local threshold is crossed. Its state may differ across client replicas; one instance opening does not establish a fleet-wide decision. Recovery requires a limited trial path, often called half-open, before normal traffic resumes. A cached fallback can preserve part of the user experience but must not be counted as a successful live dependency call.",
    "A fraud-check dependency begins timing out. Bound pending requests and open the breaker when recent failures cross a tested threshold; reject or use a labeled fallback according to business policy. Once the cool-down ends, admit a small number of trial calls per client instance and cap their aggregate rate at the dependency's recovering capacity. The policy block is illustrative; reconcile it with the actual proxy or client implementation. Only real dependency responses count as probe successes. Gradually restore live traffic while watching provider latency, failure rate, pending requests, and fallback fraction. If probes fail, reopen and lengthen the next interval within a bounded policy. Test a partial failure where only one endpoint is bad, since a cluster-wide breaker may sacrifice healthy capacity. Record whether a fraud decision was skipped, delayed, or rejected; a green HTTP status from fallback does not mean equivalent protection was applied.",
    "text", "Fraud-check breaker policy\nOpen on: tested failure-rate and minimum-sample condition\nWhile open: labeled fallback or explicit rejection\nRecovery: at most 2 trial calls per client instance\nProbe success: live fraud response only\nReopen: failed trial or growing pending-request queue\nAudit field: decision_source=live|fallback|rejected",
    "Small trial batches slow recovery but avoid swamping a fragile service. Many client instances each admitting trials can collectively create a large probe burst; cap the fleet total or coordinate when needed. A fallback may add business risk and stale-data cost. Keep breaker-open duration, pending queue, probe success, and true live-decision share visible. Do not make a breaker the only overload control when the caller can still allocate unbounded waiting work.",
    ["Do not call fallback responses proof that the dependency recovered.", "Do not assume a per-instance probe limit is a fleet-wide limit.", "Do not omit a minimum sample size before opening on a failure percentage."],
    ["devops/retry-timeout-budgets", "devops/overload-shedding", "devops/synthetic-transaction-monitoring", "devops/observability-signals"],
)

lesson(
    "dependency-bulkhead-isolation", "Dependency bulkheads: stop one slow path consuming every worker",
    "Give separate call classes bounded concurrency and queues.",
    "A bulkhead reserves independent execution capacity for distinct dependency paths. Without one, a slow optional service can occupy every request thread or connection slot and block core transactions that do not need it. The isolation must include both active calls and waiting work; a limit on active calls with an unlimited pending queue merely moves the overload into memory and latency.",
    "A claims API calls a document renderer for previews and a ledger for settlement. Under renderer slowdown, keep settlement calls in a separate bounded pool with its own timeout and queue. The text contract sets test values for a disposable workload; tune them from actual request rate and latency distributions. Reject excess preview work with a clear status and retry guidance when safe, while keeping the ledger path inside its own capacity budget. Load the renderer until its queue fills and verify settlements still meet their latency target. Then load the ledger independently so the reserve is not merely unused capacity in the normal case. Watch active calls, queue depth, queue wait, rejected requests, and settlement success, grouped by dependency. Preserve end-to-end deadlines: work that waited too long in a local queue should not start after the caller has already given up.",
    "text", "Claims API concurrency partition\nDocument preview: 12 active, 24 waiting, 2-second call deadline\nLedger settlement: 8 active, 8 waiting, 4-second call deadline\nAdmission: reject when path-specific queue is full\nDeadline: include local queue wait and remote call\nAcceptance: renderer stall does not breach settlement objective",
    "Reserved capacity can sit idle and raise compute cost, but protects the core path during a dependency incident. Setting pools too small creates avoidable rejection; setting them too large can exhaust the remote service or database. A shared CPU quota, NAT gateway, or process file limit can still couple the paths even after thread pools are split. Test these shared limits as part of the isolation claim.",
    ["Do not create separate active-call limits with one unlimited shared queue.", "Do not start remote work after its end-to-end deadline has expired.", "Do not claim isolation without testing shared CPU, network, and descriptor ceilings."],
    ["devops/overload-shedding", "devops/database-pool-pressure", "devops/nat-port-allocation-pressure", "devops/retry-timeout-budgets"],
)

lesson(
    "ambiguous-cloud-create-reconcile", "Ambiguous cloud creates: reconcile before repeating a timed-out mutation",
    "Distinguish a lost response from a failed infrastructure operation.",
    "A network timeout after a cloud create request does not establish whether the provider accepted the mutation. Repeating the call with a new identity can allocate a second resource, incur cost, and leave automation state inconsistent. The recovery unit is the desired resource identity plus an idempotency token or stable tag set, not the HTTP response alone.",
    "A deployment tool creates a recovery load balancer and loses the response. Preserve the request token, configuration fingerprint, operation time, and provider request ID. Read the provider's resource inventory using the stable token or tags and inspect any asynchronous operation status. If exactly one matching resource exists, adopt its actual identifier into the state record and verify listeners, network attachment, and health before proceeding. If none exists after a bounded consistency window, retry with the same idempotency identity when the API supports it. If two matches exist or ownership is uncertain, stop and require a reviewed reconciliation; deleting either one automatically could remove live traffic. The text block specifies the decision tree without pretending every provider exposes identical idempotency fields. Run this as a fault-injection test by dropping the create response after the provider accepts the call. A successful local command exit is not the acceptance criterion; the inventory must contain one intended resource and the automation state must point to it.",
    "text", "Create reconciliation decision\nInput: desired resource key, request token, configuration digest\nRead: provider operation status and tagged inventory\nOne match: verify properties, adopt actual ID, continue\nNo match after consistency window: retry with same token\nMultiple or mismatched matches: stop for reviewed reconciliation\nAcceptance: one intended resource, one state record, healthy route",
    "Read-back calls and a bounded wait add deployment time and control-plane API usage. They are cheaper than orphaned resources or duplicate routing targets. Tags alone may be nonunique or delayed, so pair them with provider operation identifiers and exact properties. Keep reconciliation idempotent across process restarts and expose unresolved mutations in the release record. Do not run cleanup by broad name prefix during an active incident.",
    ["Do not infer a create failed solely because its response timed out.", "Do not use a fresh request token for an ambiguous retry when the API supports idempotency.", "Do not delete a suspected duplicate before checking traffic ownership."],
    ["devops/cloud-control-plane-throttling", "devops/terraform-state-and-plan", "devops/release-evidence-record", "devops/multi-region-failover"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/cloud-boundary-recovery-project"
quiz_path = "quizzes/devops-cloud-boundary-decisions"
titles[project_path] = "Project: recover a saturated cloud boundary"
titles[quiz_path] = "DevOps cloud boundary decisions"
for item in specs:
    assert all(path in titles for path in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


for heading, summary, slugs in [
    ("Cloud egress and control-plane limits", "Budget outbound connections, API requests, and deployment surge capacity.", ["nat-port-allocation-pressure", "cloud-control-plane-throttling", "provider-quota-preflight"]),
    ("Backlog and recovery traffic", "Use completion age and bounded retry traffic to protect recovery.", ["queue-age-scaling-contract", "retry-amplification-control", "circuit-breaker-recovery-probes"]),
    ("Isolation and ambiguous mutations", "Separate dependency capacity and reconcile uncertain creates.", ["dependency-bulkhead-isolation", "ambiguous-cloud-create-reconcile"]),
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
               sort_order=19200 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Trace a shared egress failure, bounded cloud rollout, queue backlog, and uncertain provider mutation.",
               difficulty="Advanced", sort_order=19290,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use a disposable account and cluster to run a claims recovery exercise. Create a synthetic receipt API, a queue worker, and a stub payment dependency with a controlled failure switch. Record normal transaction latency, provider connection count, gateway port errors, control-plane request rate, queue oldest age, and completed receipts before introducing faults. Keep all identifiers and payloads synthetic.</p>"
    "<h2>Introduce pressure at separate boundaries</h2><p>Increase short-lived outbound connections to one destination while preserving a fixed business request rate. Confirm whether the shared egress path reports port-allocation errors; restore pooling and limit concurrent dials. Start several disposable infrastructure jobs and inject throttling in the provider stub. Show that each job respects one shared mutation budget and a total retry deadline. Calculate the maximum surge plus rollback demand for instances and subnet addresses before a canary. Refuse the rollout if the recovery reserve cannot be allocated.</p>"
    "<pre><code class=\"language-text\">Cloud boundary drill gates\nEgress: real receipt succeeds; port errors return to zero\nRollout: request budget respected; no unbounded retry loop\nQuota: surge plus rollback allocation proven\nQueue: oldest eligible age falls with durable completions\nBreaker: only live probes count as recovery\nBulkhead: renderer stall does not block settlement\nCreate: one intended resource and one state record after lost reply</code></pre>"
    "<h2>Recover work without multiplying demand</h2><p>Back up the queue with 700 synthetic receipts. Raise workers only to the measured database and provider rate ceiling, then verify that oldest eligible age decreases alongside durable completions. Induce a dependency timeout with client, proxy, and worker retries initially enabled; count total provider sends per operation. Assign a single retry owner and show that the same business key survives an ambiguous result. Open the dependency breaker, admit limited real probes, and keep fallback decisions labeled. Stall an optional renderer while proving the settlement bulkhead still serves requests. Finally drop a provider create response after acceptance; inventory and adopt the single created resource before resuming.</p>"
    "<h2>Cost and verification</h2><p>Track extra API calls, compute time, queue deliveries, and temporary resource charges. Capture one timeline with original requests, retries, rejected admissions, completed receipts, and resource inventory. End the drill only when a synthetic customer receipt completes once, the queue age is within the chosen objective, the live dependency has passed probes, and the infrastructure record names exactly one intended resource. Remove disposable assets by their exact test identifiers after the evidence is retained.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not equate a smaller visible queue with completed work.</li><li>Do not call fallback traffic proof that the dependency recovered.</li><li>Do not repeat an uncertain create under a new identity.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub]))
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Cloud boundary recovery drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What can cause connection failures across several healthy services sharing one egress route?", ["NAT port allocation pressure", "A larger HTML response body", "A higher document retention period"], "A shared translation path can be the common failing resource."),
    ("What should be compared with gateway port errors?", ["New connections by destination and actual transaction failures", "Only the total count of Pods", "Only disk byte utilization"], "Destination-specific connection churn identifies the pressure source."),
    ("How is control-plane throttling different from a hard resource quota?", ["One limits request rate; the other limits allocatable capacity", "Both mean a DNS negative cache", "Both prove the requested resource already exists"], "Rate and capacity limits need different remedies."),
    ("What capacity belongs in a deployment preflight?", ["Old revision, surge, and rollback reserve together", "Only the target steady-state replicas", "Only the smallest instance type"], "Replacement and rollback may overlap with existing resources."),
    ("Which queue signal shows whether users are waiting less?", ["Oldest eligible age alongside durable completion rate", "Visible count alone", "Number of deployment manifests"], "In-flight work can hide an unchanged customer wait."),
    ("Why can nested retry policies worsen a provider outage?", ["Attempts multiply across layers", "They remove provider rate limits", "They guarantee one business effect"], "Each outer attempt can trigger several inner sends."),
    ("What counts as a successful circuit-breaker recovery probe?", ["A live dependency response", "A cached fallback response", "A locally accepted request never sent upstream"], "Fallback availability is separate from dependency recovery."),
    ("Why is a per-client half-open limit insufficient for a large fleet?", ["The combined trial traffic can exceed recovering capacity", "It disables every circuit breaker", "It eliminates every pending request"], "Local limits add up across instances."),
    ("What must a dependency bulkhead bound besides active calls?", ["Waiting queue and deadline", "The article reading time", "Only the DNS record TTL"], "Unbounded waiting still consumes memory and response time."),
    ("After a cloud create times out, what is the first safe step?", ["Read back operation status and matching inventory", "Immediately repeat with a new token", "Delete every similarly named resource"], "The request may have succeeded while its response was lost."),
    ("When should an ambiguous create stop for review?", ["Multiple or mismatched candidate resources are found", "Exactly one matching resource is verified", "No resource exists before any bounded wait"], "Automatic adoption or deletion is unsafe when ownership is unclear."),
    ("What proves the cloud boundary drill has recovered?", ["A completed synthetic transaction and one reconciled resource", "Only a healthy Pod state", "Only an enabled autoscaler"], "User effects and infrastructure state both need evidence."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on shared egress, quotas, backlog, retries, isolation, and uncertain creates.",
            sort_order=19300, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the conclusion supported by measured work, provider responses, and reconciled resource state. A configured control is not the same as a completed recovery.</p><h2>Review these lessons</h2>" + links(project_related) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-host-protocol-failures", "quizzes/devops-release-safety"]) + "<h3>Common Mistakes</h3><ul><li>Do not mistake a cached fallback for a live dependency response.</li><li>Do not retry a cloud create before checking whether it succeeded.</li></ul>"
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Cloud boundary check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/egress-dns-contract": ["devops/nat-port-allocation-pressure"],
    "devops/terraform-state-and-plan": ["devops/cloud-control-plane-throttling", "devops/ambiguous-cloud-create-reconcile"],
    "devops/node-autoscaling-headroom": ["devops/provider-quota-preflight"],
    "devops/queue-consumer-reliability": ["devops/queue-age-scaling-contract"],
    "devops/retry-timeout-budgets": ["devops/retry-amplification-control", "devops/circuit-breaker-recovery-probes"],
    "devops/overload-shedding": ["devops/dependency-bulkhead-isolation"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))

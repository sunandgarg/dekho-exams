"""Add DevOps host, protocol, and delayed-work failure lessons."""

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
    "cpu-throttling-diagnosis", "CPU throttling: distinguish a quota ceiling from node contention",
    "Read cgroup counters before increasing replicas or blaming a slow dependency.",
    "A container CPU limit is enforced by restricting how much CPU time its cgroup can consume in a scheduling period. A process can be throttled while the node still has spare cores and while average CPU usage looks modest. CPU requests affect scheduling and relative shares; limits cap bursts. Long request latency caused by a tight CPU quota can be mistaken for network or database delay.",
    "A claims API performs signature verification during a batch of uploads. Its p95 latency rises, but database time stays flat. In a Linux container using cgroup v2, read cpu.stat and compare changes in nr_throttled and throttled_usec over a measured interval. The shell commands are read-only; the cgroup path may differ on another runtime. Correlate the counter delta with request rate, CPU usage, and user latency rather than declaring every throttled period an incident. In a disposable load test, raise the limit while keeping the request budget and replica count fixed, then check whether latency falls. If the node itself is saturated, a higher limit may steal CPU from neighbors. If the workload is bursty, a realistic request and a tested limit can preserve headroom without forcing every burst into a hard ceiling. Record the node type and architecture so a CPU comparison uses comparable hardware.",
    "bash", "cat /sys/fs/cgroup/cpu.stat\nkubectl top pod -n claims -l app=claims-api\nkubectl get pod -n claims -l app=claims-api -o wide",
    "More CPU capacity or looser limits can raise compute cost and neighbor contention. More replicas may help independent requests but will not remove a per-request CPU bottleneck and can exhaust database sessions. A throttling counter alone gives no user impact; inspect its rate next to latency and error signals. Repeat the same load profile after a change. If the cgroup uses another version or hierarchy, use the corresponding runtime counters rather than assuming this file exists.",
    ["Do not infer spare container CPU from spare node CPU when a quota is active.", "Do not increase replicas before checking the database connection budget.", "Do not treat one nonzero throttle counter as proof of current user impact."],
    ["devops/kubernetes-resource-budgets", "devops/capacity-load-testing", "devops/hpa-stabilization-boundaries", "devops/database-pool-pressure"],
)

lesson(
    "file-descriptor-exhaustion", "File descriptor exhaustion: find the leak before raising the limit",
    "Measure open sockets and files against the service limit during real traffic.",
    "A process uses file descriptors for files, sockets, pipes, and other kernel objects. When it reaches its per-process open-file limit, new opens can fail even when the host has free memory and disk space. Raising the limit may postpone the failure, but a leaking connection or unclosed file can consume the new allowance too. A gateway with many keep-alive connections also needs a deliberate capacity budget rather than an arbitrary maximum.",
    "A document API reports intermittent connection failures after several hours of traffic. On a Linux host using systemd, read its main PID, process limits, and descriptor count with the shell fragment. The commands are read-only; use a namespace-aware equivalent when the service runs in a container. Sample the count over time and classify descriptors through a bounded inspection of /proc or a diagnostic tool. Compare the trend with active clients, connection pool size, and deployment age. Reproduce the workload in a disposable environment and close the request body stream and upstream response in every path, including timeout and exception paths. Then confirm the descriptor count returns toward baseline after a traffic burst. If the service legitimately needs more concurrent connections, change the service and host limits together, account for memory per connection, and test the load balancer's own connection ceiling.",
    "bash", "process_id=$(systemctl show -p MainPID --value document-api.service)\ncat \"/proc/$process_id/limits\"\nfind \"/proc/$process_id/fd\" -mindepth 1 -maxdepth 1 | wc -l",
    "Each open connection consumes kernel and often application memory. A higher file limit can improve legitimate concurrency but can also let a leak damage the host more deeply before failing. Frequent full descriptor enumeration has a cost on busy processes; use it for diagnosis, not a high-frequency metric scrape. Track open descriptors, accept failures, and user request errors together. Restarting the process clears its descriptors temporarily but does not repair the leak.",
    ["Do not raise the open-file limit as the only fix for a rising leak.", "Do not count disk free space as evidence that descriptors are available.", "Do not omit timeout and exception paths when checking resource closure."],
    ["devops/linux-service-diagnostics", "devops/graceful-pod-shutdown", "devops/database-pool-pressure", "devops/observability-signals"],
)

lesson(
    "inode-exhaustion-recovery", "Inode exhaustion: diagnose a full filesystem with free bytes",
    "Separate file-count pressure from byte usage and delete only owned, recoverable data.",
    "A filesystem can have free data blocks but no free inodes for new files. Many small files, spool entries, or log fragments can exhaust its file-count capacity. Applications then fail to create files despite a byte-usage dashboard reporting room. In a container, the affected filesystem may be an overlay, a writable volume, or a node-level store; the right cleanup owner depends on which one is full.",
    "An invoice exporter writes one temporary file per item and leaves files behind after failed uploads. On the affected host or mounted volume, compare byte and inode usage with the read-only commands. Count files in the exporter-owned spool only after identifying its mount; a recursive count can itself be expensive on a severely loaded filesystem. Capture a sample of file age and ownership before cleanup. Stop new export intake, move recoverable work to the documented queue, and remove only files that the application has marked complete. Then verify a synthetic export can create, upload, and delete its temporary file. A restart may move the failure to another node while leaving the original disk full. Set a retention and cleanup policy with an alert on inode use and oldest incomplete export age; byte alerts alone will miss the next incident.",
    "bash", "df -h /var/lib/invoice-exporter\ndf -i /var/lib/invoice-exporter\nfind /var/lib/invoice-exporter/spool -maxdepth 1 -type f | wc -l",
    "Removing completed files returns inodes but can erase evidence if the completion state is uncertain. Larger filesystems or fewer files per batch may increase storage cost and operational complexity. Recursive scans consume I/O and may worsen an incident; prefer application counters or bounded directory inspection during routine monitoring. Track both inode and byte utilization, plus work-item age, so the alert points to business impact rather than a single storage number.",
    ["Do not conclude a filesystem has room because df reports free bytes.", "Do not delete spool files before determining whether their work completed.", "Do not run repeated full-tree scans on a failing volume."],
    ["devops/linux-service-diagnostics", "devops/node-pressure-eviction", "devops/log-pipeline-retention", "devops/queue-consumer-reliability"],
)

lesson(
    "clock-skew-operational-check", "Clock skew: verify time before debugging credentials and leases",
    "Use synchronized time for certificate validity, signed requests, and lease decisions.",
    "Clock skew is the difference between a machine's clock and a trusted time reference. A clock that is too far ahead or behind can make a valid certificate appear expired or not yet valid, can invalidate time-bounded credentials, and can confuse event ordering. Monotonic timers are appropriate for elapsed deadlines; wall-clock timestamps are needed for external validity windows but depend on synchronization.",
    "A claims worker begins rejecting short-lived service tokens after a host replacement. Before rotating every credential, read UTC time and the time service's tracking state on both the issuing and consuming hosts. The shell fragment uses chrony on a Linux host; use the installed time service's equivalent elsewhere. Compare measured offset and synchronization status with the token's issued-at and expiry fields without logging the token itself. Check whether the VM resumed from a paused state or lost its time source. Restore time synchronization through the approved host procedure, then issue a new test token and verify one authorized request. If lease ownership changed during the skew, inspect the old holder and durable effects before resuming work; simply correcting the clock does not undo operations performed under a disputed lease. Alert on offset beyond the system's tested tolerance, not a guessed universal number.",
    "bash", "date -u\nchronyc tracking\nchronyc sources -v",
    "A highly available time service uses network and operational effort, but avoids failures that otherwise look like unrelated TLS, identity, or scheduling faults. Aggressive clock stepping can disturb applications that use wall time for intervals; test the host procedure. Keep token lifetimes short enough for security needs yet longer than expected network and clock uncertainty. Record offset, last synchronization, and failed authorization rate together. Do not copy credential contents into the incident record while investigating time.",
    ["Do not rotate every secret before checking host time when many tokens fail together.", "Do not use wall-clock subtraction for local elapsed-time deadlines.", "Do not assume clock correction reverses effects of a disputed lease."],
    ["devops/certificate-renewal-path", "devops/federated-workload-identity", "devops/secret-rotation-rollout", "devops/partition-rebalance-safety"],
)

lesson(
    "dns-negative-cache-cutover", "DNS negative caching: avoid creating a name after clients already asked for it",
    "Account for cached missing-name answers when introducing an endpoint.",
    "DNS resolvers can cache negative answers such as a name not existing. If clients query a hostname before its record is created, some resolvers may keep returning the cached negative answer until its negative cache lifetime expires. Lowering the positive record's TTL later does not clear that previous absence. A record visible from an authoritative server can therefore remain invisible to clients using a recursive resolver.",
    "A settlement service will start calling a new payout endpoint. Publish the record before deploying clients that reference it, then query the authoritative name servers and multiple recursive resolvers from relevant networks. The shell sample checks an illustrative test name and its zone metadata; substitute the approved domain before use. Record whether a failed lookup occurred before creation and inspect the zone's negative-cache settings and observed resolver response. If a resolver still returns the prior negative answer, keep the old route or gate the client rollout until it expires. Test the actual TLS and application path after resolution, because an A record alone does not prove service health. Do not repeatedly create and remove the same hostname during a cutover test; the removal can seed more negative caches. Keep a rollback name available that was published ahead of time.",
    "bash", "dig payout-new.aitrove.test A\ndig payout-new.aitrove.test A @1.1.1.1\ndig aitrove.test SOA",
    "Publishing names ahead of demand uses little runtime capacity but requires coordination with certificate issuance and route preparation. Waiting for negative caches slows a cutover, while switching clients early creates connection errors despite a correct authoritative zone. Resolver implementations can cap cache lifetimes, so measure from the networks that matter rather than assuming one global expiry. Alert on client lookup failures and successful external transactions, not only authoritative record state.",
    ["Do not assume a new positive TTL clears cached NXDOMAIN answers.", "Do not deploy clients before the name and route are ready.", "Do not call one authoritative lookup proof of client resolution."],
    ["devops/dns-cutover-safety", "devops/dns-tls-edge", "devops/egress-dns-contract", "devops/synthetic-transaction-monitoring"],
)

lesson(
    "connection-drain-boundary", "Connection draining: let in-flight work finish while new traffic moves",
    "Coordinate endpoint removal, process shutdown, and persistent client connections.",
    "Connection draining stops new work from reaching a terminating instance while allowing bounded in-flight work to finish. Removing a Pod from ready endpoints does not instantly close established TCP or HTTP/2 connections, and an upstream proxy may reuse a connection until it learns the endpoint is leaving. The application, service mesh, and load balancer each have a separate timeout and shutdown behavior.",
    "A claims API holds a long-running upload for forty seconds while a rollout replaces its Pod. Inspect EndpointSlice conditions and Pod termination state with the read-only commands during a disposable rollout. The terminating endpoint is not ready for regular traffic, but an existing connection can still carry work. On termination, stop accepting new requests, advertise shutdown to keep-alive clients where the protocol permits it, and allow the upload to finish before the process exits. Set a grace period longer than measured high-percentile in-flight duration plus proxy propagation margin, while keeping an explicit upper bound so a stuck upload cannot block rollout forever. Exercise a client that reuses one connection and a client that opens a new connection mid-rollout. Verify no completed upload is silently duplicated and that a new request reaches a healthy Pod. A readiness probe returning failure alone does not demonstrate the established-connection path.",
    "bash", "kubectl get endpointslices -n claims -l kubernetes.io/service-name=claims-api -o yaml\nkubectl get pods -n claims -l app=claims-api -o wide\nkubectl describe deployment -n claims claims-api",
    "A longer grace period preserves in-flight work but uses old-Pod capacity and slows replacement. A shorter period speeds rollout while increasing aborted uploads or duplicate retries. Keep connection idle timeout, request deadline, proxy drain period, and Pod termination grace consistent. Measure active requests and client errors by revision during rollout. Retries must retain the original operation key because a connection failure can happen after the server committed an effect.",
    ["Do not assume endpoint removal closes already established connections.", "Do not set the Pod grace period shorter than the tested drain path.", "Do not retry an ambiguous write with a new operation key."],
    ["devops/graceful-pod-shutdown", "devops/kubernetes-probes", "devops/gateway-api-routing", "devops/retry-timeout-budgets"],
)

lesson(
    "queue-visibility-lease", "Queue visibility leases: prevent overlapping workers on one message",
    "Extend long-running work deliberately and keep its business effect idempotent.",
    "A queue visibility lease hides a received message from other consumers for a bounded period. If processing continues after that period, the message can be delivered again while the first worker is still running. Extending visibility reduces overlap but can delay recovery when the worker is stuck. At-least-once delivery can also duplicate a message for other reasons, so lease management cannot replace effect idempotency.",
    "A media worker transcodes a claims attachment, with normal jobs finishing in under ninety seconds and rare jobs taking several minutes. Start with a measured visibility duration, renew it only while the worker is making progress, and cap the total processing window. The text block is a worker contract, not a broker API call. Store the original attachment operation key alongside the output record, and make the final publish step conditional on that key not already being completed. Crash the worker immediately after publishing output but before acknowledging the message; the next delivery must observe the completed effect and acknowledge without publishing again. Then pause a worker long enough for its lease to expire and confirm overlapping deliveries cannot both commit. Track oldest visible age, in-flight count, renewal failures, and dead-letter arrivals. If the job is permanently invalid, move it to a reviewed failure path after a bounded attempt count rather than renewing forever.",
    "text", "Attachment worker lease\nMeasured normal duration: below 90 seconds\nVisibility: 150 seconds to start\nRenewal: only with observed progress; total cap 8 minutes\nEffect key: original attachment operation ID\nPublish: conditional on absent completed effect\nAcknowledge: after durable output and completion record",
    "A long lease reduces duplicate overlap but increases time before another worker can recover abandoned work. Frequent renewals add broker traffic and failure handling. An early acknowledgement improves throughput at the cost of lost work if the process fails before persisting output. Choose lease duration from actual processing distributions, keep the effect guard, and test both crash windows. A zero duplicate count in a short test does not establish exactly-once delivery.",
    ["Do not let processing routinely outlive visibility without renewal.", "Do not acknowledge before the output is durable.", "Do not assign a new business key on redelivery."],
    ["devops/queue-consumer-reliability", "devops/dead-letter-replay", "devops/partition-rebalance-safety", "devops/retry-timeout-budgets"],
)

lesson(
    "object-replication-recovery", "Object replication: verify the exact recovery object arrived",
    "Treat asynchronous copy status as part of the recovery point, not as a bucket setting.",
    "Object-store replication copies eligible objects to another destination after source writes. A configured replication rule does not mean every new object has already arrived; an item can be pending or fail. A recovery procedure that switches readers to the secondary bucket before required objects complete may serve missing data even when the primary reported a successful write.",
    "A claims archive copies signed payout statements to another region. When a statement is written, retain its object key, version identifier, digest, and business operation ID in a durable index. The shell sample inspects one source object's replication status using a provider CLI; it is read-only and assumes an approved account and bucket. Before a regional cutover, compare a manifest of required versions against destination inventory and verify several objects by digest and application parse. Put failed or pending objects on an explicit recovery list; a bucket-level replication configuration is not evidence for a particular statement. During a drill, stop writes or establish a precise cutover position, then check every operation acknowledged before that position has its required object version in the recovery region. Preserve delete-marker semantics and retention controls so a mistaken source deletion cannot silently remove the only usable copy.",
    "bash", "aws s3api head-object --bucket claims-primary-archive --key statements/2026/10/payout-47.json --query '{version:VersionId,replication:ReplicationStatus,bytes:ContentLength}'\naws s3api head-object --bucket claims-recovery-archive --key statements/2026/10/payout-47.json --query '{version:VersionId,bytes:ContentLength}'",
    "Cross-region copies consume storage and transfer budget and can lag under failure or high write volume. Checking each object at write time adds API cost; use a manifest and sampled continuous checks, then exhaustive reconciliation at a defined recovery boundary. A destination HEAD response proves existence and metadata, not that the application can parse the object or that it matches the required version. Measure age and count of pending or failed copies against the recovery-point objective.",
    ["Do not equate an enabled replication rule with completed copy of every object.", "Do not compare only object keys when versions matter.", "Do not promote a recovery region without reconciling acknowledged writes."],
    ["devops/backup-and-recovery", "devops/immutable-backup-retention", "devops/multi-region-failover", "devops/replica-lag-read-contract"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/host-protocol-failure-project"
quiz_path = "quizzes/devops-host-protocol-failures"
titles[project_path] = "Project: recover a host and protocol failure chain"
titles[quiz_path] = "DevOps host and protocol failure decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


groups = [
    ("Host exhaustion and time", "Diagnose quota, descriptor, inode, and clock failures before changing the service.", ["cpu-throttling-diagnosis", "file-descriptor-exhaustion", "inode-exhaustion-recovery", "clock-skew-operational-check"]),
    ("Name and connection lifetime", "Account for cached absence and persistent connections during rollout.", ["dns-negative-cache-cutover", "connection-drain-boundary"]),
    ("Delayed work and recovery objects", "Guard long-running queue work and verify copied recovery data.", ["queue-visibility-lease", "object-replication-recovery"]),
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
               sort_order=19000 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Trace quota and file pressure, validate DNS and connection draining, then recover leased work and copied objects.",
               difficulty="Advanced", sort_order=19090,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project_related = ["devops/cpu-throttling-diagnosis", "devops/file-descriptor-exhaustion", "devops/inode-exhaustion-recovery", "devops/clock-skew-operational-check", "devops/dns-negative-cache-cutover", "devops/connection-drain-boundary", "devops/queue-visibility-lease", "devops/object-replication-recovery"]
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>This drill exercises a synthetic claims upload path across a host, a public name, and an asynchronous recovery copy. Use a disposable cluster, test records, and a dedicated object bucket. Capture the baseline request latency, cgroup CPU counters, open descriptors, inode availability, clock offset, queue age, and object-copy status before making changes.</p>"
    "<h2>Induce and distinguish failures</h2><p>Apply a low CPU limit to one test Pod and show throttling grows while node capacity remains available. Open and close enough test connections to reveal descriptor growth, then create small disposable spool files until an inode alert fires without deleting unprocessed work. Offset the clock in an isolated host or simulated time environment and observe a test token validity failure; restore synchronization before continuing. Query a hostname before its record exists, create it, and compare authoritative and recursive answers. During a rollout, hold a long upload on a reused connection and verify its result after the old endpoint stops receiving new traffic.</p>"
    "<pre><code class=\"language-text\">Claims host-protocol drill\nCPU: throttled time delta and p95 latency\nFiles: descriptor count and inode use before/after cleanup\nTime: offset and test-token acceptance\nDNS: cached missing-name answer and eventual success\nDrain: one long upload completes exactly once\nQueue: lease expiry yields one durable effect\nRecovery: required object version copied and parsed</code></pre>"
    "<h2>Recover delayed work</h2><p>Hold one attachment transcode beyond its initial visibility window. Renew while progress continues, then crash after durable output but before acknowledgement; the next delivery must reuse the original operation key. Write an archive object and inspect the exact version in both source and recovery stores. Delay replication and confirm the disaster-recovery gate refuses a cutover while the required version is pending. Once copied, compare digest and application parse result before marking the recovery point complete.</p>"
    "<h2>Cost and verification</h2><p>The drill spends test compute, queue deliveries, object-copy traffic, and diagnostic time. Record the added latency, descriptor and inode recovery, DNS negative-cache duration, interrupted connection count, duplicate effect count, and object-copy lag. A green Pod status or enabled replication rule alone does not satisfy the acceptance criteria. Remove only disposable resources after the evidence is stored under the team's retention policy.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not treat free disk bytes as free inodes.</li><li>Do not assume an endpoint change closes existing connections.</li><li>Do not acknowledge a queue message before its output is durable.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub]))
rows.append(project)
project_index = by_path[project_hub]
project_index["data"]["modules"][0]["lessons"].append(project_path)
project_index["body"] += "<h2>Host and protocol failure drill</h2>" + links([project_path])
project_index["updated_at"] = stamp

questions = [
    ("What can make one container slow while its node has spare CPU?", ["A hard cgroup CPU quota throttles the container", "Every idle node is automatically overcommitted", "A DNS TTL caps CPU time"], 0, "A container quota can bind before node-wide capacity does."),
    ("What does reaching the open-file limit block?", ["New files or sockets for that process", "Only deletion of old log lines", "All disk block allocation on every host"], 0, "Descriptors cover sockets and files."),
    ("Why can a filesystem reject new files while bytes remain free?", ["Its inodes are exhausted", "Its positive DNS TTL expired", "Its image tag changed"], 0, "File-count capacity differs from byte capacity."),
    ("What should be checked when many short-lived tokens fail on one host?", ["Host time offset and synchronization state", "Only the backup retention period", "Only the HPA replica count"], 0, "Clock skew can invalidate otherwise valid credentials."),
    ("Why may a newly created DNS name still fail for some clients?", ["A resolver cached its previous negative answer", "An authoritative record always clears all caches", "TLS sends the A record to every resolver"], 0, "Negative answers can persist until their cache lifetime ends."),
    ("What can remain active after a Pod is removed from ready endpoints?", ["An established client connection and in-flight request", "Only newly opened connections", "No work of any kind"], 0, "Endpoint routing and established connections have separate lifetimes."),
    ("What happens if processing outlasts a queue visibility lease?", ["Another worker can receive the same message", "The first worker's effect becomes atomic", "The broker guarantees the task completed"], 0, "The lease controls redelivery, not business-effect completion."),
    ("What does an enabled object-replication rule fail to prove?", ["A particular required version already arrived", "The source bucket has a rule", "The destination was configured"], 0, "Individual copies can still be pending or failed."),
    ("Why is merely raising a file limit risky when descriptors keep growing?", ["A leak can consume the larger allowance too", "It always lowers memory use", "It closes existing sockets"], 0, "The underlying leak remains."),
    ("What should follow an inode cleanup?", ["A synthetic create, process, and delete path succeeds", "Only a larger byte-usage alert threshold", "Immediate deletion of unprocessed spool files"], 0, "Recovery needs an application-level check."),
    ("What should a retry keep after an ambiguous upload connection failure?", ["The original operation key", "A new business key", "Only the current Pod name"], 0, "The server may have committed before the client saw a response."),
    ("What belongs in the recovery-object gate?", ["Required key and version, copy state, digest, and parse result", "Only the bucket-level replication setting", "Only the source object count"], 0, "Recovery depends on exact usable objects."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve checks on CPU, files, time, DNS, connections, leases, and recovery objects.",
            sort_order=19100, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(answer - index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, answer, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the operational conclusion supported by the observed state. The questions distinguish a configured control from a proven user or recovery result.</p><h2>Review these lessons</h2>" + links(project_related) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-release-safety", "quizzes/devops-failure-boundaries", "quizzes/devops-system-boundaries"]) + "<h3>Common Mistakes</h3><ul><li>Do not treat a configured queue lease as exactly-once execution.</li><li>Do not treat a source object as proof that its recovery copy exists.</li></ul>"
rows.append(quiz)
quiz_index = by_path[quiz_hub]
quiz_index["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_index["body"] += "<h2>Host and protocol check</h2>" + links([quiz_path])
quiz_index["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": target, "title": titles[target]} for target in [project_path, quiz_path])

for source, targets in {
    "devops/kubernetes-resource-budgets": ["devops/cpu-throttling-diagnosis"],
    "devops/linux-service-diagnostics": ["devops/file-descriptor-exhaustion", "devops/inode-exhaustion-recovery"],
    "devops/certificate-renewal-path": ["devops/clock-skew-operational-check"],
    "devops/dns-cutover-safety": ["devops/dns-negative-cache-cutover"],
    "devops/graceful-pod-shutdown": ["devops/connection-drain-boundary"],
    "devops/queue-consumer-reliability": ["devops/queue-visibility-lease"],
    "devops/multi-region-failover": ["devops/object-replication-recovery"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1,
                  "new_quiz_banks": 1, "total_records": len(rows)}))

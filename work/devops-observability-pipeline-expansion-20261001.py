"""Add observability-pipeline failure lessons to the local DevOps preview."""

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
    "scrape-staleness-absence", "Scrape staleness: separate a failed target from a missing target",
    "Detect both unreachable exporters and targets that vanished from discovery.",
    "A Prometheus scrape failure and a missing target are different states. A discovered target that cannot be scraped normally reports an up sample of zero. When discovery stops reporting that target, its series can become stale and disappear from an instant query. An alert based only on up equal to zero therefore misses a target removed from discovery. The monitoring system also needs an inventory expectation or an independent user-path check; an absent series cannot prove which workload disappeared.",
    "A receipt API has three intended instances. During a routing incident, one instance still appears in discovery but refuses connections; later a bad discovery label removes all instances from the scrape job. Compare target inventory with an expected deployment count before choosing the alarm. The expression below covers a failed scrape and the complete absence of recent up samples for the job, using a seven-minute window selected for this exercise. Test both faults separately. Check the scrape interval, target relabeling, and rule evaluation interval, then measure when the alert becomes active and when a synthetic receipt request fails. If only one of three targets disappears, the job-level absence branch stays false; a separate expected-instance signal or service-discovery audit is required. Do not fill missing measurements with zero in the SLO calculation without first deciding whether the service or the telemetry path failed.",
    "promql", 'up{job="receipt-api"} == 0 or absent_over_time(up{job="receipt-api"}[7m])',
    "The absence window trades speed for resistance to short scrape interruptions. A very short window pages during a planned target shuffle; a long window delays detection of a monitoring blind spot. The expression scans recent up samples, while an expected-replica rule requires additional state. Check query output under both faults and verify a separate user-path signal, because green telemetry collection can coexist with a broken checkout or receipt endpoint.",
    ["Do not infer service health from a series that disappeared from the query.", "Do not use a job-level absence test to claim that every individual replica is present.", "Do not turn missing telemetry into successful requests in an SLO denominator."],
    ["devops/observability-signals", "devops/synthetic-transaction-monitoring", "devops/alert-design", "devops/slo-burn-rate-alerts"],
)

lesson(
    "histogram-slo-bucket-design", "Latency histograms: put a bucket at the actual SLO threshold",
    "Count successful requests inside the latency boundary across every replica.",
    "A classic Prometheus histogram exports cumulative bucket counters, a count, and a sum. A bucket whose upper bound matches the latency objective can count requests that met it. Per-process summary quantiles cannot be averaged into a correct service-wide percentile. The bucket layout is part of the instrumentation contract: once a threshold is missing, a dashboard cannot reconstruct its exact count from adjacent buckets.",
    "A receipt API promises that successful requests finish within 470 milliseconds. Instrument one duration histogram on every serving instance with a bucket at 0.47 seconds and a bounded outcome label. The query below divides fast successful observations by all observed requests, so errors also consume the request budget. Confirm the metric actually has the stated bucket and outcome labels before using it. Compare the result with synthetic requests and access-log counts over the same five-minute range; missing instances and scrape failures can bias both numerator and denominator. During a canary, aggregate the same metric by revision to expose a slow cohort before relying on the fleet total. Keep a separate traffic-volume guard so a service with almost no observations does not look confidently healthy. If the objective changes, update instrumentation and rollout compatibility before switching the alert expression.",
    "promql", 'sum(rate(receipt_request_duration_seconds_bucket{le="0.47",outcome="success"}[5m])) / sum(rate(receipt_request_duration_seconds_count[5m]))',
    "Each extra classic bucket creates more time series for every label combination, raising scrape, storage, and query cost. Too few buckets hide the objective boundary; too many compound a cardinality problem. A five-minute rate reacts quickly but becomes noisy for low traffic. The fraction is meaningful only if every request enters the count and the success label is set consistently. Compare counts across replicas and test a known slow request rather than trusting a smooth percentile graph.",
    ["Do not average precomputed per-instance quantiles to report fleet latency.", "Do not claim an exact threshold fraction when no matching bucket was emitted.", "Do not exclude errors from both sides of a user-facing request SLO without stating that policy."],
    ["devops/service-level-objectives", "devops/metric-cardinality-budget", "devops/canary-cohort-analysis", "devops/scrape-staleness-absence"],
)

lesson(
    "prometheus-remote-write-backlog", "Remote-write backlog: budget the gap between local samples and long-term storage",
    "Treat a remote endpoint outage as a bounded replay problem.",
    "Prometheus remote write reads local write-ahead-log data and sends batches through per-destination queues. When a remote endpoint slows, pending samples and retry work grow. Queue size and shard count consume memory; more shards can also overwhelm the receiver. Local scraping can remain healthy while the long-term store falls behind, so a green target dashboard does not prove that remote queries contain the same recent history.",
    "A metrics archive for settlement services stops accepting writes for a maintenance hour. Record the incoming sample rate, pending-sample trend, remote send rate, WAL disk headroom, and time of the oldest missing sample. The fragment names the pending-sample signal; filter it by destination labels when a deployment has several remotes. During the outage, keep local Prometheus available for immediate triage, and avoid increasing queue capacity or shard count until memory and receiver capacity are measured. Restore the destination, then verify pending samples drain and compare a known counter increase in both local and remote queries for the same bounded interval. A successful HTTP response from the remote endpoint is insufficient if older samples were already lost to retention or rejected as out of order. Document the longest tolerable endpoint outage for the installed Prometheus version and configured WAL retention; do not copy a generic duration into an operational promise.",
    "promql", "prometheus_remote_storage_samples_pending",
    "A larger queue can absorb bursts but raises memory use; more parallel requests raise CPU and network cost on both sides. Recovery time depends on the difference between remote drain throughput and the new incoming sample rate, not only the backlog size. If the remote can send 18,000 samples per second while 15,000 arrive, a 5.4-million-sample backlog needs about thirty minutes to drain, ignoring retries and batching overhead. Prove the missing interval through a source-versus-remote query before closing the incident.",
    ["Do not treat scrape success as proof that long-term storage received the samples.", "Do not raise shard count without checking receiver saturation and Prometheus memory.", "Do not call the gap recovered merely because the pending gauge reached zero."],
    ["devops/observability-signals", "devops/metric-cardinality-budget", "devops/alert-design", "devops/capacity-load-testing"],
)

lesson(
    "otel-collector-queue-budget", "Collector export queues: measure the failure budget before telemetry is dropped",
    "Distinguish receiver success, queued data, retry expiry, and backend acceptance.",
    "An OpenTelemetry Collector exporter can queue telemetry while its destination is slow or unreachable. In-memory buffering is lost on a collector crash; a persistent queue can survive a restart but still has finite disk and retry limits. A receiver accepting a span is therefore not the same as the backend storing it. The Collector's own queue size, capacity, enqueue-failure, and send-failure metrics reveal where that guarantee ends.",
    "A trace gateway receives 4,200 spans per second. Its exporter can send only 2,700 while the backend is degraded. Measure the queue in batches and the average spans per batch before translating capacity to time: a queue sized for 300,000 spans fills in about 200 seconds at a 1,500-span-per-second deficit. The expression below reports queue occupancy as a fraction for matching exporter label sets; confirm the exact metric names and labels on the installed Collector distribution. Inject a backend outage in an isolated environment, then observe queue growth, failed enqueues, retry attempts, and the last trace visible at the destination. If retention across a collector restart is required, test a persistent queue on a disk with a separate capacity alert. Restart the gateway while the queue contains known trace IDs and verify those IDs arrive once the backend returns. The acceptance record must state whether duplicates, drops, or both can occur after a timeout.",
    "promql", "otelcol_exporter_queue_size / clamp_min(otelcol_exporter_queue_capacity, 1)",
    "Memory queues compete with the collector's processors and receiver for heap. Persistent queues spend disk writes and can fail when that disk is full. Batching lowers request overhead but makes each queued item larger, so count-based queue capacity alone is not a byte budget. Scaling gateways can spread new traffic but does not recover data already dropped. Measure both queue occupancy and destination acceptance under sustained load.",
    ["Do not equate a successful OTLP receive with durable backend storage.", "Do not call a disk-backed queue unlimited or assume it survives a failed disk.", "Do not size capacity from batch count without measuring batch size and retry time."],
    ["devops/trace-context-propagation", "devops/trace-sampling-decisions", "devops/observability-signals", "devops/prometheus-remote-write-backlog"],
)

lesson(
    "tail-sampling-trace-affinity", "Tail sampling at scale: keep every span of a trace with one decision maker",
    "Route by trace identity before adding stateful sampling replicas.",
    "Tail sampling waits for enough of a trace to arrive before deciding whether to keep it. That allows a policy to retain error or slow traces, but the collector must hold spans and decision state during the wait. A round-robin balancer can split one trace across collectors; each replica then sees an incomplete history and may reach a different decision. A trace-aware routing tier keeps spans with the same trace ID together, while late spans and replica changes still need an explicit policy.",
    "A payment service emits traces across an API, a queue consumer, and a ledger writer. Place a routing tier before two sampling gateways and send all spans for a given trace ID to the same gateway. Generate a slow trace, an error trace, and a normal trace; verify that each retained trace contains the expected cross-service spans. Now restart one gateway during the decision wait and record which traces become partial or are lost. Keep the decision window long enough for typical queue delay, but do not assume it can cover an unbounded async workflow. Measure memory consumed by traces awaiting a decision, the rate of spans arriving after a decision, and routing imbalance. Use span links for separate asynchronous work rather than forcing unrelated operations under one trace ID. If the routing topology changes, retest decisions before using sampled traces as incident evidence.",
    "text", "Tail-sampling acceptance record\nRouting key: trace ID, stable across gateway tier\nPolicy: keep error and slow traces, sample normal traces\nDecision wait: compared with measured async span delay\nRestart drill: partial-trace rate and lost-decision count\nLate span rule: recorded and tested\nAcceptance: expected spans present for retained test traces",
    "A longer decision wait raises memory use and delays trace availability. More sampling gateways add routing and state-transfer risk; they do not automatically improve a trace-aware decision. Keeping every slow trace can produce a surge when the whole service slows, so capacity needs a degraded-mode policy. Compare full-trace completeness and collector memory under both ordinary and incident load.",
    ["Do not round-robin individual spans into independent tail samplers.", "Do not assume a retained root span proves the whole async operation was captured.", "Do not choose a decision wait without measuring late-span behavior."],
    ["devops/trace-sampling-decisions", "devops/trace-context-propagation", "devops/partition-rebalance-safety", "devops/otel-collector-queue-budget"],
)

lesson(
    "alertmanager-routing-inhibition", "Alert routing and inhibition: suppress symptoms without silencing the cause",
    "Keep root-cause pages distinct from dependent symptoms and time-limited maintenance silence.",
    "Alertmanager groups, routes, and inhibits alerts after rules fire. Grouping reduces duplicate notifications for related alerts. Inhibition can suppress a symptom only while a designated source alert matches the same scope. A silence is a separate, time-bounded matcher used for known maintenance. Broad matchers can hide unrelated failures, and a route that sends a page to the wrong owner can make a correct detection operationally useless.",
    "A settlement cluster loses database connectivity. Twenty instance-level failure alerts fire alongside one cluster-level database alert. Configure a reviewed policy that routes the source alert to the database owner and inhibits only instance symptoms in the same cluster while that source is active. The text fragment is a policy contract, not a complete Alertmanager configuration. In a staging alert stream, inject the source and symptoms in two clusters, then confirm the second cluster still pages. Remove the source alert and prove symptoms become notifiable again. Test grouping delay against the service's page-time objective; waiting too long for a root alert can delay a real page. For maintenance, create a narrowly scoped silence with an expiry and an owner, then verify it cannot match future clusters. Keep an independent notification path for a complete Alertmanager outage.",
    "text", "Settlement alert policy\nRoot alert: DatabaseUnavailable, owner database on-call\nSymptom alert: SettlementInstanceUnavailable\nInhibit only when cluster labels are equal\nGroup by cluster and alert name; retain affected instance list\nMaintenance silence: named owner, narrow matcher, expiry\nTest: other cluster still pages; source removal restores symptom page",
    "Grouping saves responder attention but may delay the first notification. Inhibition lowers noise while the source is visible; if source detection fails, symptoms must still route. A broad silence can hide a separate incident at almost no compute cost, which makes review and expiry more important than config size. Measure page latency, duplicate notifications, false suppression, and unowned routes in the staging test.",
    ["Do not inhibit symptoms across clusters because their alert names match.", "Do not make a maintenance silence permanent or ownerless.", "Do not assume alert-rule evaluation proves the notification reached a human."],
    ["devops/alert-design", "devops/slo-burn-rate-alerts", "devops/incident-response", "devops/scrape-staleness-absence"],
)

lesson(
    "monitoring-ha-dedup-contract", "Monitoring redundancy: keep duplicate collectors without double-counting requests",
    "Separate scrape high availability from query deduplication and page delivery.",
    "Two independent Prometheus servers can scrape the same targets so one server outage does not erase live visibility. Each server may send a copy of the samples to remote storage and a copy of firing alerts to Alertmanager. A remote query layer must identify replicas before deduplicating their samples; Alertmanager handles identical alert notifications through its own grouping and deduplication path. Neither behavior follows merely from deploying two replicas.",
    "Run two scrape servers for the receipt API on separate nodes. Give their remote samples a stable cluster identity and distinct replica identities, then configure the long-term query layer's deduplication rule explicitly. Send identical alert labels to every configured Alertmanager peer and test one scrape-server shutdown followed by one Alertmanager-peer shutdown. Query the receipt request counter before and after each fault: the service total must not double while both scrapers run, and it must not drop to zero when one stops. Compare alert receipt and notification logs with the expected page count. During an Alertmanager network partition, duplicate notifications may be preferable to missing a page; document that behavior for on-call staff. Keep both scrape targets and both alert routes under configuration review, or an apparently redundant pair may share the same failure domain.",
    "text", "Receipt monitoring HA contract\nScrape pair: separate nodes and independent local storage\nExternal identity: one cluster, two distinct replica values\nRemote query: tested replica deduplication rule\nAlert labels: identical across scrape replicas\nAlertmanager: each Prometheus targets every peer\nFault tests: one scraper down, one alert peer down, partition\nAcceptance: counter neither doubles nor disappears; page still arrives",
    "A second scraper roughly doubles scrape and local storage work and may duplicate remote-write traffic. Query deduplication reduces double-counting but can mask a replica with partial data if its rules are not understood. More alert peers add network and state-management work. Measure real query counts and page delivery during faults; a green HA topology diagram is not evidence.",
    ["Do not add a replica label to alert identity if identical alerts must deduplicate.", "Do not assume remote storage removes duplicate samples without an explicit rule.", "Do not put a single load balancer in front of the only Alertmanager peer list."],
    ["devops/observability-signals", "devops/prometheus-remote-write-backlog", "devops/alertmanager-routing-inhibition", "devops/incident-response"],
)

lesson(
    "telemetry-sensitive-data-boundary", "Telemetry redaction: remove sensitive fields before an exporter or sampler sees them",
    "Treat spans, logs, and metric labels as data copies with their own retention path.",
    "Telemetry can contain credentials, customer identifiers, request bodies, and network addresses even when an application database has access controls. A collector-side attribute processor can remove named span attributes, but it cannot make data safe if the application already put a secret in a span name, exception message, log body, or metric label. The safest boundary is instrumentation that never emits those values; collector processing is a second check before export.",
    "A payout request accidentally records an authorization header and a customer email as trace attributes. Change instrumentation to emit a bounded route template and payment-state label instead of raw request data. In an isolated collector pipeline, remove the two named attributes before batching or export; the YAML fragment shows only the processor portion and needs receivers, exporters, and a pipeline to run. Send a synthetic canary token through a test request, then search exported spans, logs, metrics, and collector diagnostics for that exact token. Keep the test token non-privileged and short-lived. Verify that a failed export queue or debug logger does not retain a raw copy. If historical telemetry contains the field, handle its retention and access as an incident rather than declaring it fixed by a new processor. Review each new instrumentation library for defaults that add headers or user IDs.",
    "yaml", "processors:\n  attributes/payout_scrub:\n    actions:\n      - key: http.request.header.authorization\n        action: delete\n      - key: user.email\n        action: delete",
    "Allowing fewer attributes can lower storage and indexing cost, but broad deletion can also remove the join key an incident needs. Define safe correlation fields before changing the pipeline. Hashing a predictable identifier may still permit reidentification, and a regex scrub can miss an unexpected encoding. Sample a test payload through every telemetry signal and inspect the exported result, not only the collector configuration. Redaction should occur before durable queues whenever the Collector topology permits it.",
    ["Do not rely on span-attribute deletion to scrub log bodies or metric labels.", "Do not use a hash of a small predictable ID as proof of anonymity.", "Do not keep a debug exporter enabled with raw payment telemetry in production."],
    ["devops/log-pipeline-retention", "devops/trace-context-propagation", "devops/metric-cardinality-budget", "devops/otel-collector-queue-budget"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/observability-pipeline-failure-project"
quiz_path = "quizzes/devops-observability-pipeline-decisions"
titles[project_path] = "Project: recover an observability pipeline without hiding user impact"
titles[quiz_path] = "DevOps observability pipeline decisions"
for item in specs:
    assert all(path in titles for path in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


for heading, summary, slugs in [
    ("Truth in service measurements", "Detect missing targets and count requests at the latency boundary.", ["scrape-staleness-absence", "histogram-slo-bucket-design"]),
    ("Telemetry transport under failure", "Budget remote-write and Collector backlogs before data is lost.", ["prometheus-remote-write-backlog", "otel-collector-queue-budget"]),
    ("Trace and alert decisions", "Keep traces together and route root-cause pages to their owner.", ["tail-sampling-trace-affinity", "alertmanager-routing-inhibition"]),
    ("Monitoring trust boundaries", "Test redundant monitoring and remove sensitive fields before export.", ["monitoring-ha-dedup-contract", "telemetry-sensitive-data-boundary"]),
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
               sort_order=20000 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Fault-inject scrape discovery, remote export, trace routing, paging, and redaction.",
               difficulty="Advanced", sort_order=20090,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Build a disposable receipt API, two scrape servers, a remote metrics store, an OpenTelemetry Collector tier, and a staging alert receiver. Send synthetic requests with known success, error, and latency outcomes. Record target discovery, local and remote request counts, export queue occupancy, sampled trace completeness, first-page latency, and the absence of test secrets before injecting faults. Keep test tokens non-privileged and the environment isolated from real on-call routes.</p>"
    "<h2>Break the measurement path</h2><p>Make one exporter unreachable, then remove its job from discovery; prove that scrape-failure and absence checks respond differently. Issue slow and failed requests against two API replicas and calculate the fast-success fraction from a 470-millisecond histogram bucket. Stop the remote metrics receiver while local scraping continues. Record pending samples and WAL headroom, restore the receiver, and compare the same bounded counter range in local and remote queries. Degrade the trace destination separately: measure Collector queue growth and failed enqueues, restart a gateway with queued test trace IDs, and verify which IDs arrive after recovery.</p>"
    "<pre><code class=\"language-text\">Observability failure acceptance gates\nScrape: failed target and absent job detected separately\nLatency: fast-success fraction matches known synthetic requests\nRemote metrics: bounded interval reconciles after backlog drains\nCollector: queue limit, retry expiry, and dropped spans recorded\nTrace: retained slow and error traces contain expected spans\nAlerts: root pages; only same-cluster symptoms inhibited\nHA: request counter does not double with two scrapers\nPrivacy: canary token absent from exported signals and diagnostics</code></pre>"
    "<h2>Test decisions and ownership</h2><p>Split spans for one slow trace across sampling gateways, then restore trace-ID routing and compare trace completeness. Fire a database root alert with settlement symptoms in two clusters; only the matching cluster's symptoms may be inhibited. Take down one scraper and one Alertmanager peer and verify a page still arrives without doubling the remote request total. Inject a synthetic authorization token and customer email through the receipt path; inspect spans, logs, metric labels, exporter queues, and diagnostics before accepting the redaction boundary. Keep an independent synthetic request result as the user-impact reference whenever telemetry is missing.</p>"
    "<h2>Cost and verification</h2><p>Estimate queue fill time from measured input and drain rates, not a guessed batch size. Record extra storage and network cost from duplicate scrapers, page delay from alert grouping, memory from trace decision waits, and the operational consequence of every missing interval. The drill passes only when the last trustworthy measurement interval is named, a page reaches its intended owner, and no canary token appears in exported data. A dashboard returning values is not enough.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not count absent targets as healthy requests.</li><li>Do not call a remote-write queue empty proof that every old sample arrived.</li><li>Do not route each span of one trace to a different stateful sampler.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Observability pipeline failure drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What does up equal to zero indicate for a discovered target?", ["The scrape failed", "The target was removed from all discovery", "The SLO has no traffic"], "A failed scrape can produce up equal to zero while the target remains discovered."),
    ("What catches a job that stopped producing up samples entirely?", ["An absence check over an appropriate range", "Only up equal to zero", "A larger request histogram"], "A stale series can disappear from an instant query instead of reporting zero."),
    ("Why place a classic histogram bucket at the latency objective?", ["It permits an exact count at that boundary", "It makes every query cost-free", "It replaces error classification"], "A missing boundary cannot be reconstructed exactly from neighboring cumulative buckets."),
    ("Why can local scraping be healthy while remote metrics are stale?", ["Remote write has its own queue and receiver", "Histogram buckets block all scrapes", "Alertmanager owns the local WAL"], "Collection and remote acceptance are separate steps."),
    ("What determines how long a remote backlog takes to clear?", ["Drain throughput minus ongoing arrival rate", "Only the number of scrape targets", "Only the local query window"], "New samples continue arriving while the queue drains."),
    ("What does a Collector receiver acknowledgement fail to prove?", ["The backend stored the telemetry", "The Collector accepted the request", "A trace ID was present"], "Export queues and retries sit between receipt and backend storage."),
    ("What makes a persistent Collector queue finite?", ["Disk space, queue limits, and retry policy", "Only an API route label", "The browser cache"], "Persistence survives some restarts but cannot defeat full disks or expired retries."),
    ("How should spans reach stateful tail-sampling replicas?", ["By trace-ID affinity", "By independent round robin per span", "By log line length"], "A sampler needs enough of one trace to make one decision."),
    ("What scope should inhibit a cluster's instance symptoms?", ["A matching root alert in the same cluster", "Any alert with the same severity anywhere", "Every alert during business hours"], "Broad matching can hide a separate cluster failure."),
    ("What is required when two scrapers send the same samples remotely?", ["A tested replica deduplication rule", "Only matching dashboard colors", "A longer scrape interval"], "Redundant scrapes otherwise risk double-counted queries."),
    ("Why might a partitioned Alertmanager pair send duplicate pages?", ["It favors delivery during a network split", "It stops evaluating every rule", "It changes metric bucket bounds"], "A duplicate page can be safer than a missed incident notification."),
    ("Why is deleting a span attribute insufficient for sensitive-data control?", ["The value may remain in logs, names, labels, or old storage", "Every exporter ignores the processor", "The deleted field becomes a histogram"], "Each emitted signal and retained copy requires inspection."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on telemetry gaps, queues, sampling, paging, redundancy, and privacy.",
            sort_order=20100, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the decision that preserves a trustworthy user-impact signal when the telemetry system itself is degraded. A green dashboard is not evidence if collection or export has a gap.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-data-continuity-decisions", "quizzes/devops-cluster-control-failures"])
    + "<h3>Common Mistakes</h3><ul><li>Do not equate local collection with remote acceptance.</li><li>Do not silence every symptom across unrelated clusters.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Observability pipeline check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/observability-signals": ["devops/scrape-staleness-absence", "devops/prometheus-remote-write-backlog"],
    "devops/service-level-objectives": ["devops/histogram-slo-bucket-design"],
    "devops/trace-sampling-decisions": ["devops/tail-sampling-trace-affinity"],
    "devops/alert-design": ["devops/alertmanager-routing-inhibition"],
    "devops/trace-context-propagation": ["devops/otel-collector-queue-budget"],
    "devops/synthetic-transaction-monitoring": ["devops/monitoring-ha-dedup-contract"],
    "devops/log-pipeline-retention": ["devops/telemetry-sensitive-data-boundary"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))

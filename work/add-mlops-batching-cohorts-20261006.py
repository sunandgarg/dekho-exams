"""Add inference scheduling and cohort-outcome release operations."""
from de_batch_publisher import publish

M = 'mlops/'
BATCH = 'Live inference batching and queue control'
COHORT = 'Cohort outcome evidence and fairness review'
lessons = [
    {
        'path': M + 'live-inference-batching-and-deadline-budget',
        'title': 'Live inference batching: spend queue time inside a request deadline',
        'module': BATCH, 'project': False,
        'summary': 'A live inference batch combines compatible requests, but its queue wait must fit inside each caller’s remaining deadline.',
        'sections': [
            ('Account for the whole request', 'A parcel-damage model runs on a shared accelerator. The service can process several photographs together, so batching may improve device use, yet a request spends time in admission, preprocessing, queueing, inference, postprocessing and network delivery. Set the caller deadline before choosing a batch wait. Reserve a measured margin for everything after the queue. [[mlops/inference-latency-budget-and-tail-observation|The latency budget]] separates those stages; a fast model kernel does not rescue a caller whose queue already consumed the deadline.'),
            ('Release on size or age', 'Use a bounded maximum batch size and a maximum wait measured from the oldest queued request. A full compatible batch can leave immediately. At low traffic, release a partial batch when the oldest request reaches its wait limit. A scheduler that waits for every batch to fill makes off-peak callers pay indefinitely for throughput that never arrives. Check the oldest request’s absolute deadline before adding a new one; the queue must not admit work that cannot plausibly complete.'),
            ('Measure the trade with realistic arrivals', 'Compare single-request serving with several batch limits under both steady and bursty arrivals. Report requests per second, achieved batch-size distribution, queue p50 and p99, end-to-end p95 and p99, deadline misses, rejected work and device utilization. A larger batch can reduce compute per request while increasing queue age or memory pressure. Measure the actual shape mix: photographs with different decode and resize costs can shift the bottleneck before inference begins. [[mlops/model-cache-warmup-and-capacity-planning|Warmup and capacity]] alter the result; [[mlops/batch-shape-compatibility-and-tail-protection|shape control]] prevents one large payload from dominating a group.'),
            ('Keep an escape route', 'If the queue is near saturation, reject early or use a separately approved lower-cost route rather than accepting a doomed request. Pin scheduler settings and model digest together for canary comparison. Roll back on sustained deadline misses even if average throughput rises. [[mlops/shadow-canary-and-rollback|Canary rules]] need both tail latency and error rate; [[mlops/parcel-live-batching-project|the parcel project]] tests a burst after the initial benchmark.'),
        ],
        'code': '''def release_batch(queue, now_ms, max_size, max_wait_ms, reserve_ms):
    if not queue:
        return [], "empty"
    if max_size < 1 or max_wait_ms < 0 or reserve_ms < 0:
        raise ValueError("invalid scheduler budget")
    oldest = queue[0]
    expiry_ms = oldest["deadline_ms"] - reserve_ms
    if now_ms >= expiry_ms:
        return [], "reject:deadline"
    if len(queue) >= max_size or now_ms - oldest["arrival_ms"] >= max_wait_ms:
        return queue[:max_size], "release"
    return [], "wait"

waiting = [{"request_id": "parcel-47", "arrival_ms": 100,
            "deadline_ms": 190}]
assert release_batch(waiting, 121, 4, 20, 38)[1] == "release"
assert release_batch(waiting, 160, 4, 20, 38)[1] == "reject:deadline"
''',
        'cost': 'Inspecting the oldest entry and slicing a released batch costs O(b) time and space for b released requests. A queue with constant-time append and removal avoids repeatedly shifting a Python list in a real server. Batching can improve device throughput while adding queue delay and temporary activation memory; profile the whole path at representative concurrency.',
        'mistakes': ['Measuring kernel time while omitting queue and preprocessing time.', 'Waiting for a full batch when traffic falls below the expected rate.', 'Accepting a request whose remaining deadline cannot cover execution.', 'Promoting a throughput gain after p99 deadline misses rise.'],
        'related': [M + 'batch-shape-compatibility-and-tail-protection', M + 'parcel-live-batching-project', M + 'inference-latency-budget-and-tail-observation', M + 'model-cache-warmup-and-capacity-planning', M + 'shadow-canary-and-rollback'],
    },
    {
        'path': M + 'batch-shape-compatibility-and-tail-protection',
        'title': 'Batch shape compatibility: prevent large requests from setting every caller’s cost',
        'module': BATCH, 'project': False,
        'summary': 'Batching works only when requests share a valid input contract and the cost of padding or preprocessing remains bounded.',
        'sections': [
            ('Define what can share execution', 'The parcel model accepts photographs after resizing, but one client also sends panoramic scans. A batch must share model digest, preprocessing revision, tensor layout and any state constraint. It is unsafe to combine requests merely because they reached the same endpoint. A stateful sequence may need ordered affinity, while a stateless classifier can often group independent requests. [[mlops/inference-request-response-contracts|Request contracts]] should make these differences explicit before scheduler policy is tuned.'),
            ('Control the largest-item penalty', 'A text model may pad a batch to its longest sequence. If three short claims enter alongside a long document, all four slots can pay for the long length. Group by a small number of length or shape buckets, cap accepted payload size and measure useful tokens or pixels against processed tokens or pixels. Buckets add fragmentation: a rare shape may wait longer. Set a maximum queue age per bucket, then let a partial batch proceed instead of violating a caller deadline. [[mlops/inference-payload-and-compute-admission|Admission checks]] bound the worst single request.'),
            ('Track fairness across request classes', 'A single first-in queue can let expensive scans delay small image requests. Separate priority lanes only for an approved service contract, with capacity reserved so lower-priority work does not starve. Measure queue time and deadline misses per size bucket and client class with bounded metric labels. Do not include raw client IDs in high-cardinality monitoring. [[mlops/monitoring-cardinality-and-metric-identities|Metric identity rules]] keep dashboards usable; [[mlops/live-inference-batching-and-deadline-budget|the deadline policy]] remains the governing constraint.'),
            ('Test failure and ordering', 'Exercise a malformed payload, an oversize scan, a canceled request and a batch that partially fails. Every result must be mapped back to its request ID; batch order is not a safe substitute when stages can retry or cancel independently. Record which requests were rejected before execution and which failed after execution. [[mlops/idempotent-inference-retries-and-quotas|Retry controls]] prevent a timeout from multiplying device load. In [[mlops/parcel-live-batching-project|the project]], a panoramic scan is isolated without quietly dropping small parcels.'),
        ],
        'code': '''def compatible_groups(requests, max_pixels):
    groups = {}
    rejected = []
    for request in requests:
        if request["pixels"] > max_pixels:
            rejected.append(request["request_id"])
            continue
        shape_bucket = "large" if request["pixels"] > 350_000 else "small"
        key = (request["model_digest"], request["preprocess_rev"], shape_bucket)
        groups.setdefault(key, []).append(request["request_id"])
    return groups, rejected

requests = [
    {"request_id": "parcel-47", "pixels": 210_000,
     "model_digest": "damage-r7", "preprocess_rev": "resize-3"},
    {"request_id": "parcel-48", "pixels": 890_000,
     "model_digest": "damage-r7", "preprocess_rev": "resize-3"},
    {"request_id": "scan-49", "pixels": 2_100_000,
     "model_digest": "damage-r7", "preprocess_rev": "resize-3"},
]
groups, rejected = compatible_groups(requests, 1_000_000)
assert sorted(len(group) for group in groups.values()) == [1, 1]
assert rejected == ["scan-49"]
''',
        'cost': 'Grouping n requests is O(n) expected time and O(n) storage. A real scheduler also pays queue bookkeeping and may lose batching efficiency when shape buckets are too fine. The benefit must be weighed against padding cost, deadline misses and memory use under the actual traffic distribution.',
        'mistakes': ['Grouping different preprocessing or model revisions because the endpoint name matches.', 'Letting one long or large item determine compute for every small request.', 'Creating so many buckets that rare shapes wait past their deadlines.', 'Returning results by batch position after cancellations or retries change order.'],
        'related': [M + 'live-inference-batching-and-deadline-budget', M + 'parcel-live-batching-project', M + 'inference-payload-and-compute-admission', M + 'inference-request-response-contracts', M + 'monitoring-cardinality-and-metric-identities'],
    },
    {
        'path': M + 'parcel-live-batching-project',
        'title': 'Project: tune parcel-damage inference for bursts and mixed image sizes',
        'module': BATCH, 'project': True,
        'summary': 'Choose a bounded batch policy, measure queue tails and reject a configuration that gains throughput by missing caller deadlines.',
        'sections': [
            ('Specify the serving contract', 'A sorting-center camera calls a parcel-damage classifier and needs a result within 190 milliseconds. Keep 38 milliseconds for preprocessing, postprocessing and transport after the queue. Each request carries arrival time, deadline, image size, model digest and preprocessing revision. A scan above the approved pixel limit is rejected before scheduling. [[mlops/inference-payload-and-compute-admission|Payload admission]] keeps the queue from becoming a storage area for unbounded work.'),
            ('Benchmark candidate schedulers', 'Run a single-request baseline, a small batch with a short wait and a larger batch with a longer wait. Replay both steady traffic and a scanner-restart burst. For each policy record achieved batch sizes, useful versus padded pixels, queue p99, end-to-end p99, deadline misses and GPU memory. The long-wait policy wins requests per second during a steady run but fails the restart burst. Keep the shorter wait even though its median device utilization is lower. [[mlops/live-inference-batching-and-deadline-budget|Deadline accounting]] decides this trade.'),
            ('Handle mixed sizes', 'Separate normal photographs from the panoramic scan shape bucket. The two normal requests can batch; the panorama has an explicit size cap and, if allowed, its own queue age. Test a cancellation while a batch is forming, then verify response IDs and retry tokens still identify the original caller. [[mlops/batch-shape-compatibility-and-tail-protection|Compatibility policy]] avoids processing several small images at panorama cost.'),
            ('Canary and handoff', 'Pin scheduler settings alongside the model and resize revision. Send a small traffic share to the candidate and compare per-bucket tail latency, deadline misses, rejection reasons and classification quality against the incumbent. Set a rollback owner and a hard miss-rate gate before traffic rises. Deliver the benchmark packet, selected policy, rejected alternative and rollback evidence. [[mlops/shadow-canary-and-rollback|The canary workflow]] treats this as a serving release, not a mere configuration tweak.'),
        ],
        'code': '''def batching_release_gate(candidate, incumbent, limits):
    if candidate["quality_recall"] < limits["minimum_recall"]:
        return "hold:quality"
    if candidate["deadline_miss_rate"] > limits["maximum_miss_rate"]:
        return "hold:deadline"
    if candidate["queue_p99_ms"] > incumbent["queue_p99_ms"] + limits["queue_regression_ms"]:
        return "hold:queue-tail"
    return "canary:bounded-batch"

limits = {"minimum_recall": 0.84, "maximum_miss_rate": 0.012,
          "queue_regression_ms": 9}
incumbent = {"queue_p99_ms": 24}
slow = {"quality_recall": 0.88, "deadline_miss_rate": 0.026,
        "queue_p99_ms": 42}
fast = {"quality_recall": 0.88, "deadline_miss_rate": 0.008,
        "queue_p99_ms": 31}
assert batching_release_gate(slow, incumbent, limits) == "hold:deadline"
assert batching_release_gate(fast, incumbent, limits) == "canary:bounded-batch"
''',
        'cost': 'The aggregate gate is O(1) time and space once benchmark reports exist. The expensive part is load replay across arrival patterns and image-size buckets; production batching also consumes queue memory. A faster steady-state throughput figure is not worth a missed camera deadline during predictable restart bursts.',
        'mistakes': ['Benchmarking only a smooth arrival stream.', 'Selecting the largest batch from utilization alone.', 'Ignoring rejection and cancellation paths in response-ID mapping.', 'Rolling out a scheduler change without a separate tail-latency rollback gate.'],
        'related': [M + 'live-inference-batching-and-deadline-budget', M + 'batch-shape-compatibility-and-tail-protection', M + 'inference-latency-budget-and-tail-observation', M + 'shadow-canary-and-rollback', M + 'inference-payload-and-compute-admission'],
    },
    {
        'path': M + 'cohort-outcome-monitoring-and-denominator-contracts',
        'title': 'Cohort outcome monitoring: keep denominators and observation windows visible',
        'module': COHORT, 'project': False,
        'summary': 'Group outcome rates are operational evidence only when the eligible population, label maturity and missing-group policy are explicit.',
        'sections': [
            ('Define the harm and population', 'A delivery-claim triage model flags claims for manual review. The review team asks whether genuine claims from different service regions are being missed at different rates. False-negative rate among label-mature genuine claims addresses that question; overall approval or alert rate answers another. Define region from the approved request record, the eligible claim population, decision time and label-maturity interval before computing any gap. [[mlops/selective-label-observation-and-audit-sampling|Selective labels]] can make reviewed cases look like the whole population when they are not.'),
            ('Keep every denominator', 'For each region, store eligible cases, cases with mature ground truth, true positives, false negatives and unobserved outcomes. A rate without these counts hides how little evidence supports it. Treat missing region as an explicit unknown cohort with a count; do not assign it to the largest known region. If a cohort has no mature positive cases, its false-negative rate is undefined, not zero. Preserve protected or sensitive attributes only under approved access and retention. [[mlops/inference-logging-privacy|Logging limits]] still apply.'),
            ('Compare like with like', 'Use the same time window, label definition, threshold and model version across groups. A rollout that routes regions to different revisions needs version-stratified analysis before a pooled comparison. Show uncertainty or at least minimum-count gates for small cohorts; one additional miss can move a tiny group’s rate sharply. An observed gap triggers review, not an automatic explanation of cause. [[mlops/slice-quality-gates-and-uncertainty|Slice uncertainty]] and [[mlops/label-corrections-and-evaluation-ledger|label correction records]] are part of the evidence trail.'),
            ('Escalate a bounded finding', 'Tie the monitor to an owner who can examine label collection, threshold policy, regional operations and model error. Keep the current result as a dated measurement with its denominators and known blind spots. Do not declare a system fair from a single parity number. [[mlops/cohort-gap-release-and-remeasurement|Release review]] compares candidate and incumbent on the same frame; [[mlops/claim-region-outcome-review-project|the project]] catches a false improvement caused by missing outcomes.'),
        ],
        'code': '''def false_negative_rate_by_region(cases):
    counts = {}
    for case in cases:
        region = case.get("region") or "unknown"
        bucket = counts.setdefault(region, {"positives": 0, "misses": 0,
                                            "unobserved": 0})
        if not case["label_mature"]:
            bucket["unobserved"] += 1
        elif case["genuine_claim"]:
            bucket["positives"] += 1
            bucket["misses"] += not case["flagged"]
    return {region: {**bucket, "false_negative_rate":
            bucket["misses"] / bucket["positives"] if bucket["positives"] else None}
            for region, bucket in counts.items()}

cases = [
    {"region": "north", "label_mature": True, "genuine_claim": True, "flagged": False},
    {"region": "north", "label_mature": True, "genuine_claim": True, "flagged": True},
    {"region": None, "label_mature": False, "genuine_claim": False, "flagged": False},
]
report = false_negative_rate_by_region(cases)
assert report["north"]["false_negative_rate"] == 0.5
assert report["unknown"]["false_negative_rate"] is None
''',
        'cost': 'Scanning n cases costs O(n) time and O(g) storage for g region groups. At scale, preaggregated counts reduce dashboard work, but their provenance must retain model version and label window. Manual review of uncertain or missing outcomes costs more than the arithmetic and is necessary for a credible release decision.',
        'mistakes': ['Reporting group percentages without eligible and label-mature counts.', 'Treating a group with zero mature positive cases as a zero-error group.', 'Pooling model revisions and thresholds into one apparent trend.', 'Inferring the cause of a gap from the metric alone.'],
        'related': [M + 'cohort-gap-release-and-remeasurement', M + 'claim-region-outcome-review-project', M + 'slice-quality-gates-and-uncertainty', M + 'selective-label-observation-and-audit-sampling', M + 'label-corrections-and-evaluation-ledger'],
    },
    {
        'path': M + 'cohort-gap-release-and-remeasurement',
        'title': 'Cohort release gates: compare harm, coverage and uncertainty together',
        'module': COHORT, 'project': False,
        'summary': 'A release gate must account for measured group harm, incomplete outcomes and the cost of an operational change.',
        'sections': [
            ('Select a decision rule before comparison', 'A candidate claim model changes its score threshold. Define the target harm, overall capacity, group minimum counts and maximum acceptable group gap before seeing its holdout result. A strict equality target is not automatically the right metric: the review team cares about missed genuine claims while also being able to handle the alert volume. Record who chose the policy and what population it covers. [[mlops/cohort-outcome-monitoring-and-denominator-contracts|Denominator contracts]] make the comparison interpretable.'),
            ('Separate lack of evidence from a pass', 'If a region has only a few mature genuine claims, the apparent gap is unstable. Hold the cohort judgment as insufficient evidence and use an approved audit sample or longer observation window. Do not bury that region in an overall metric. If labels are collected mostly for flagged claims, estimate the observation bias before calling an unflagged case negative. [[mlops/selective-label-observation-and-audit-sampling|Audit sampling]] can reveal the unseen part of the workflow.'),
            ('Test a candidate across constraints', 'Compare candidate and incumbent with the same label definition, review-capacity limit, cohort membership and time window. Check overall recall, each region’s false-negative rate, alert volume, missing-region share and confidence or count threshold. A candidate may lower the maximum group gap by making every region worse. Reject that outcome even when the parity number improves. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] prevent an aggregate win from masking local harm.'),
            ('Release with remeasurement', 'If the evidence passes, canary by stable assignment and keep model revision in the event ledger. Watch group counts and mature outcomes after the canary; delayed labels mean early dashboards cannot claim a quality win. Set an owner, a data-collection action for insufficient cohorts and a rollback trigger for a confirmed harm increase. [[mlops/drift-delayed-label-monitoring|Delayed-label monitoring]] defines when the quality window closes. [[mlops/claim-region-outcome-review-project|The project]] holds a seemingly better candidate whose unknown-region share grows.'),
        ],
        'code': '''def cohort_release_gate(candidate, limits):
    if candidate["unknown_region_share"] > limits["maximum_unknown_share"]:
        return "hold:coverage"
    if min(candidate["mature_positives"].values()) < limits["minimum_positives"]:
        return "hold:insufficient-evidence"
    if candidate["overall_recall"] < limits["minimum_recall"]:
        return "hold:overall-harm"
    rates = list(candidate["false_negative_rates"].values())
    if max(rates) - min(rates) > limits["maximum_gap"]:
        return "review:cohort-gap"
    if candidate["daily_alerts"] > limits["alert_capacity"]:
        return "hold:capacity"
    return "canary:remeasure"

limits = {"maximum_unknown_share": 0.08, "minimum_positives": 40,
          "minimum_recall": 0.84, "maximum_gap": 0.12, "alert_capacity": 420}
candidate = {"unknown_region_share": 0.11,
             "mature_positives": {"north": 68, "south": 57},
             "overall_recall": 0.88,
             "false_negative_rates": {"north": 0.10, "south": 0.16},
             "daily_alerts": 390}
assert cohort_release_gate(candidate, limits) == "hold:coverage"
assert cohort_release_gate({**candidate, "unknown_region_share": 0.04},
                           limits) == "canary:remeasure"
''',
        'cost': 'The gate scans g cohorts in O(g) time and O(g) temporary space. Longer label windows, approved audit sampling and human review cost far more than the metric calculation. A count threshold is a triage rule, not a substitute for an uncertainty estimate or an investigation of missing outcomes.',
        'mistakes': ['Optimizing only the disparity number while every group loses recall.', 'Passing a tiny cohort because its observed rate happens to look good.', 'Treating missing group membership as random without checking its pattern.', 'Declaring the canary successful before delayed labels mature.'],
        'related': [M + 'cohort-outcome-monitoring-and-denominator-contracts', M + 'claim-region-outcome-review-project', M + 'slice-quality-gates-and-uncertainty', M + 'drift-delayed-label-monitoring', M + 'selective-label-observation-and-audit-sampling'],
    },
    {
        'path': M + 'claim-region-outcome-review-project',
        'title': 'Project: review regional claim outcomes before a model release',
        'module': COHORT, 'project': True,
        'summary': 'Rebuild regional denominators, challenge a parity improvement and publish a delayed-label remeasurement plan.',
        'sections': [
            ('Frame the decision', 'A claim-review service flags suspicious delivery claims, but the operations team wants genuine claims to reach a reviewer. The candidate model appears to reduce the largest regional false-negative gap. Before accepting it, pin the label-maturity window, region definition, score threshold, model revision and maximum daily alert capacity. The objective is missed genuine claims under a real review limit, not a decorative parity score. [[mlops/cohort-outcome-monitoring-and-denominator-contracts|The cohort contract]] provides each numerator and denominator.'),
            ('Find the missing cases', 'The first dashboard omits claims without region metadata and uses only closed reviews as ground truth. Unknown-region share rises from four to eleven percent under the candidate, and unflagged claims are much less likely to be reviewed. Mark the comparison incomplete. Request an approved random audit sample of unflagged claims and repair the region mapping where source evidence permits; keep unresolved entries as unknown. [[mlops/selective-label-observation-and-audit-sampling|Observation bias]] cannot be fixed by assuming an unlabeled claim was legitimate or illegitimate.'),
            ('Compare harm and capacity', 'After the label window matures, compute each region’s false negatives among genuine claims, with positive-case counts and uncertainty. Check overall recall and alerts per day. A second candidate narrows the gap because both regions become worse; reject it. If one region has too few mature positives, hold that slice as insufficient evidence rather than averaging it away. [[mlops/cohort-gap-release-and-remeasurement|The gate]] returns a separate disposition for coverage, evidence, harm and capacity.'),
            ('Prepare a cautious canary', 'For a passing candidate, assign traffic consistently, retain model revision in the decision ledger and name an operations reviewer. Set a maturity date for the first quality comparison; early telemetry may report latency, missing-region share and alert load but not a final false-negative result. Keep a rollback trigger for a confirmed rise in missed claims and an action to expand audit coverage. [[mlops/drift-delayed-label-monitoring|Delayed-label monitoring]] and [[mlops/shadow-canary-and-rollback|canary practice]] close the handoff.'),
        ],
        'code': '''def claim_review_disposition(report, limits):
    if report["unknown_region_share"] > limits["unknown_share"]:
        return "hold:region-coverage"
    if report["audit_sample_completed"] is False:
        return "hold:outcome-observation"
    if min(report["mature_positive_counts"].values()) < limits["min_count"]:
        return "hold:small-cohort"
    if report["candidate_recall"] < report["incumbent_recall"]:
        return "hold:more-missed-claims"
    if report["daily_alerts"] > limits["daily_capacity"]:
        return "hold:review-capacity"
    return "canary:with-maturity-date"

limits = {"unknown_share": 0.08, "min_count": 40,
          "daily_capacity": 420}
report = {"unknown_region_share": 0.11, "audit_sample_completed": True,
          "mature_positive_counts": {"north": 68, "south": 57},
          "candidate_recall": 0.88, "incumbent_recall": 0.86,
          "daily_alerts": 390}
assert claim_review_disposition(report, limits) == "hold:region-coverage"
assert claim_review_disposition({**report, "unknown_region_share": 0.04},
                                 limits) == "canary:with-maturity-date"
''',
        'cost': 'The gate is O(g) time for g cohort counts and O(1) extra space. Sampling unflagged claims, waiting for mature labels and reconciling region metadata dominate operational cost. Skipping those steps makes a cheap dashboard, but its apparent improvement can be driven by lost or selectively observed cases.',
        'mistakes': ['Dropping unknown-region cases to produce a cleaner comparison.', 'Using only reviewed claims to estimate misses among all genuine claims.', 'Accepting a smaller gap when both regions have worse recall.', 'Calling the first canary day a quality result before labels mature.'],
        'related': [M + 'cohort-outcome-monitoring-and-denominator-contracts', M + 'cohort-gap-release-and-remeasurement', M + 'selective-label-observation-and-audit-sampling', M + 'drift-delayed-label-monitoring', M + 'shadow-canary-and-rollback'],
    },
]

crosslinks = [
    (M + 'inference-latency-budget-and-tail-observation', M + 'live-inference-batching-and-deadline-budget'),
    (M + 'inference-payload-and-compute-admission', M + 'batch-shape-compatibility-and-tail-protection'),
    (M + 'receipt-serving-slo-project', M + 'parcel-live-batching-project'),
    (M + 'slice-quality-gates-and-uncertainty', M + 'cohort-outcome-monitoring-and-denominator-contracts'),
    (M + 'selective-label-observation-and-audit-sampling', M + 'cohort-gap-release-and-remeasurement'),
    (M + 'drift-delayed-label-monitoring', M + 'claim-region-outcome-review-project'),
]

if __name__ == '__main__':
    publish(lessons, [BATCH, COHORT], crosslinks,
            'aitrove-mlops-batching-cohorts-import-20261006.json', 6244,
            subject='mlops', hub_path=M + 'mlops-tutorial')
